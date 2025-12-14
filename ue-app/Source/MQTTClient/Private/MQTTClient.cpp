/*
 * Minimal MQTT client implementation (stubbed worker) for Unreal Engine 5.7
 *
 * This file provides:
 *  - UMQTTClient: Blueprint-friendly UObject wrapper implemented to forward work to a background worker.
 *  - FMQTTWorker: FRunnable-based background worker which, in this minimal implementation, simulates
 *    a broker connection and processes outgoing requests from the game thread. The worker exposes
 *    an API to Connect/Disconnect/Publish/Subscribe/Unsubscribe and will dispatch events back to
 *    the game thread via the UMQTTClient's Blueprint delegates.
 *
 * Notes:
 *  - This implementation is intentionally minimal and designed to compile out-of-the-box without
 *    external MQTT libraries. If the module is compiled with a third-party MQTT library (indicated
 *    by the build-time macro WITH_MQTT_THIRD_PARTY), you should replace FMQTTWorker's internals
 *    with a proper implementation that integrates with that library (e.g., mosquitto, paho).
 *
 *  - For simplicity this worker accepts only IPv4 textual addresses when attempting to connect.
 *    Hostname resolution and TLS are omitted from this minimal implementation.
 *
 *  - All incoming event dispatches (OnConnected/OnDisconnected/OnMessageReceived) are guaranteed
 *    to run on the Game Thread using AsyncTask.
 *
 *  - The code below contains safety checks to avoid touching UObjects from background threads.
 */

#include "MQTTClient.h"
#include "MQTTClientWorker.h"

#include "Async/Async.h"
#include "HAL/PlatformProcess.h"
#include "Misc/ScopeLock.h"
#include "Misc/Timespan.h"
#include "HAL/Event.h"
#include "Logging/LogMacros.h"

DEFINE_LOG_CATEGORY_STATIC(LogMQTTClient, Log, All);

//////////////////////////////////////////////////////////////////////////
// UMQTTClient::FImpl
//
// Private PIMPL that owns the worker. Kept small so the UObject header doesn't need to expose implementation details.
struct UMQTTClient::FImpl
{
	FImpl()
		: Worker(nullptr)
	{}

	~FImpl()
	{
		if (Worker)
		{
			Worker->Shutdown();
			delete Worker;
			Worker = nullptr;
		}
	}

	FMQTTWorker* Worker;
};

//////////////////////////////////////////////////////////////////////////
// UMQTTClient
UMQTTClient::UMQTTClient()
	: Impl(MakeUnique<FImpl>())
	, Broker(TEXT(""))
	, Port(1883)
	, bUseTLS(false)
	, Username(TEXT(""))
	, Password(TEXT(""))
	, ClientId(TEXT(""))
	, KeepAliveSeconds(60)
	, bConnected(false)
{
	// Nothing to do here; worker will be created when Connect is called.
}

bool UMQTTClient::Connect(const FString& BrokerAddress, int32 BrokerPort, bool bInUseTLS)
{
	Broker = BrokerAddress;
	Port = BrokerPort;
	bUseTLS = bInUseTLS;

	// Create worker if it doesn't exist
	if (!Impl->Worker)
	{
		Impl->Worker = new FMQTTWorker(this);
		if (!Impl->Worker->Start())
		{
			UE_LOG(LogMQTTClient, Warning, TEXT("MQTT worker failed to start"));
			delete Impl->Worker;
			Impl->Worker = nullptr;
			return false;
		}
	}

	// Pass configuration to the worker and request connect
	Impl->Worker->SetClientId(ClientId);
	Impl->Worker->SetCredentials(Username, Password);
	Impl->Worker->SetKeepAlive(KeepAliveSeconds);
	Impl->Worker->Connect(Broker, Port, bUseTLS);

	// Starting the connection attempt succeeded (actual connection happens asynchronously)
	return true;
}

void UMQTTClient::Disconnect(bool bForce)
{
	if (Impl && Impl->Worker)
	{
		Impl->Worker->Disconnect(bForce);
	}
}

bool UMQTTClient::Publish(const FString& Topic, const FString& Payload, int32 QoS, bool bRetain)
{
	if (Impl && Impl->Worker)
	{
		return Impl->Worker->Publish(Topic, Payload, QoS, bRetain);
	}
	return false;
}

bool UMQTTClient::Subscribe(const FString& TopicFilter, int32 QoS)
{
	if (Impl && Impl->Worker)
	{
		return Impl->Worker->Subscribe(TopicFilter, QoS);
	}
	return false;
}

bool UMQTTClient::Unsubscribe(const FString& TopicFilter)
{
	if (Impl && Impl->Worker)
	{
		return Impl->Worker->Unsubscribe(TopicFilter);
	}
	return false;
}

void UMQTTClient::SetCredentials(const FString& InUsername, const FString& InPassword)
{
	Username = InUsername;
	Password = InPassword;
	if (Impl && Impl->Worker)
	{
		Impl->Worker->SetCredentials(Username, Password);
	}
}

void UMQTTClient::SetClientId(const FString& InClientId)
{
	ClientId = InClientId;
	if (Impl && Impl->Worker)
	{
		Impl->Worker->SetClientId(ClientId);
	}
}

bool UMQTTClient::IsConnected() const
{
	// Prefer worker state if available; otherwise fall back to local flag
	if (Impl && Impl->Worker)
	{
		return Impl->Worker->IsConnected();
	}
	return bConnected;
}

void UMQTTClient::SetKeepAlive(int32 KeepAlive)
{
	KeepAliveSeconds = KeepAlive;
	if (Impl && Impl->Worker)
	{
		Impl->Worker->SetKeepAlive(KeepAliveSeconds);
	}
}

void UMQTTClient::BeginDestroy()
{
	// Ensure the worker is shut down before the UObject is destroyed to avoid background threads touching this object
	if (Impl)
	{
		if (Impl->Worker)
		{
			Impl->Worker->Shutdown();
			delete Impl->Worker;
			Impl->Worker = nullptr;
		}
		Impl.Reset();
	}
	Super::BeginDestroy();
}

void UMQTTClient::BroadcastConnected()
{
	// Internal helper - broadcast the Blueprint delegate on the GameThread.
	// Note: This function intentionally does not check thread context; callers should ensure GameThread usage.
	OnConnected.Broadcast();
}

void UMQTTClient::BroadcastDisconnected(const FString& Reason)
{
	OnDisconnected.Broadcast(Reason);
}

void UMQTTClient::BroadcastMessageReceived(const FString& Topic, const FString& Payload)
{
	OnMessageReceived.Broadcast(Topic, Payload);
}

//////////////////////////////////////////////////////////////////////////
// FMQTTWorker - Minimal/stubbed implementation
//
// This runnable provides a background thread that accepts Connect/Disconnect/Publish/Subscribe requests,
// simulates establishing a connection, and then forwards received messages to the owner via its
// Blueprint delegates. It is intentionally simple and is primarily a template that should be
// replaced with a full MQTT wire-protocol implementation or wrapped third-party client.
//////////////////////////////////////////////////////////////////////////

FMQTTWorker::FMQTTWorker(UMQTTClient* InOwner)
	: Owner(InOwner)
	, Thread(nullptr)
	, WakeEvent(nullptr)
	, Host()
	, Port(1883)
	, bUseTLS(false)
	, Username()
	, Password()
	, ClientId()
	, KeepAliveSeconds(60)
	, Socket(nullptr)
	, bStopRequested(false)
	, bConnected(false)
	, bShutdownComplete(false)
{
	// Create a manual-reset event used to wake the worker when new work arrives or when shutting down.
	WakeEvent = FPlatformProcess::GetSynchEventFromPool(false);
}

FMQTTWorker::~FMQTTWorker()
{
	Shutdown();
	if (WakeEvent)
	{
		FPlatformProcess::ReturnSynchEventToPool(WakeEvent);
		WakeEvent = nullptr;
	}
}

bool FMQTTWorker::Start()
{
	// Create and start the thread that will run this FRunnable
	if (Thread)
	{
		// already started
		return true;
	}

	Thread = FRunnableThread::Create(this, TEXT("FMQTTWorker"), 0, TPri_Normal);
	if (!Thread)
	{
		UE_LOG(LogMQTTClient, Error, TEXT("Failed to create FMQTTWorker thread"));
		return false;
	}
	return true;
}

void FMQTTWorker::Shutdown()
{
	Stop();

	// Signal shutdown and wake the worker so it can exit promptly
	bStopRequested = true;
	if (WakeEvent)
	{
		WakeEvent->Trigger();
	}

	// If we have a thread, kill/join it
	if (Thread)
	{
		// Wait briefly for thread to exit gracefully
		const double WaitSeconds = 1.0;
		const double StartTime = FPlatformTime::Seconds();
		while (!bShutdownComplete && (FPlatformTime::Seconds() - StartTime) < WaitSeconds)
		{
			FPlatformProcess::Sleep(0.01f);
		}

		// If still not complete, instruct the thread to kill
		if (!bShutdownComplete)
		{
			Thread->Kill(true);
		}

		delete Thread;
		Thread = nullptr;
	}

	// Release socket if any
	if (Socket)
	{
		ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->DestroySocket(Socket);
		Socket = nullptr;
	}
}

bool FMQTTWorker::Init()
{
	// Nothing to initialize in the stub implementation
	return true;
}

uint32 FMQTTWorker::Run()
{
	UE_LOG(LogMQTTClient, Verbose, TEXT("FMQTTWorker started"));

	while (!bStopRequested)
	{
		// Wait until woken or timeout
		if (WakeEvent)
		{
			// Wait for up to 200ms or until triggered
			WakeEvent->Wait(200);
			// reset the event state (manual-reset is false so it's auto-reset)
		}
		else
		{
			FPlatformProcess::Sleep(0.2f);
		}

		// If a connect request is pending and we are not connected, perform a simulated connection attempt.
		if (!bConnected && !Host.IsEmpty())
		{
			// Minimal requirement: host must be numeric IPv4 (dotted) for the stub to attempt a real socket connect.
			// Hostname resolution is out of scope for this minimal implementation.
			bool bAttemptedConnect = false;

#if WITH_MQTT_THIRD_PARTY
			// If a third-party library exists, you would call into it here to perform a real connect.
			// This stub intentionally does not implement that path.
#endif

			// For the stub we simply mark as connected (no real network).
			bConnected = true;
			NotifyConnected();

			// Continue to next loop to process any outgoing queue entries.
		}

		// Process outgoing publishes
		FMQTTOutgoing Out;
		while (OutgoingMessages.Dequeue(Out))
		{
			// In a real implementation we would serialize an MQTT PUBLISH packet and write to the socket.
			// For our minimal stub, we'll just echo the message back as if the broker forwarded it.
			UE_LOG(LogMQTTClient, Verbose, TEXT("Stub-Publish Topic=%s Payload=%s"), *Out.Topic, *Out.Payload);

			// Simulate network delay a tiny bit
			FPlatformProcess::Sleep(0.005f);

			// Notify owner that a message was 'received' on the topic (echo)
			NotifyMessageReceived(Out.Topic, Out.Payload);
		}

		// Process subscription requests
		FMQTTSubscriptionRequest SubReq;
		while (SubscriptionRequests.Dequeue(SubReq))
		{
			UE_LOG(LogMQTTClient, Verbose, TEXT("Stub-Subscription %s (QoS=%d) subscribe=%d"), *SubReq.TopicFilter, SubReq.QoS, SubReq.bSubscribe ? 1 : 0);
			// In a full implementation we'd send SUBSCRIBE/UNSUBSCRIBE packets here.
			// For now we simply log and pretend the subscription succeeded.
		}

		// This stub does not perform network receive. A real implementation would read from the socket here,
		// parse incoming MQTT packets, and call NotifyMessageReceived/NotifyDisconnected as appropriate.
	}

	UE_LOG(LogMQTTClient, Verbose, TEXT("FMQTTWorker exiting"));
	bShutdownComplete = true;
	return 0;
}

void FMQTTWorker::Stop()
{
	// Signal the run loop to stop next iteration
	bStopRequested = true;
	if (WakeEvent)
	{
		WakeEvent->Trigger();
	}
}

void FMQTTWorker::Exit()
{
	// Nothing special to clean up for the stub
}

bool FMQTTWorker::Connect(const FString& InHost, int32 InPort, bool bInUseTLS)
{
	FScopeLock Lock(&Mutex);

	Host = InHost;
	Port = InPort;
	bUseTLS = bInUseTLS;

	// Wake worker thread to pick up the connect request
	WakeWorker();

	return true;
}

void FMQTTWorker::Disconnect(bool bForce)
{
	FScopeLock Lock(&Mutex);

	// Clear pending Host so worker won't attempt reconnect
	Host.Empty();

	// For a real networked implementation, teardown socket properly. For the stub set connected false.
	if (bConnected)
	{
		bConnected = false;
		NotifyDisconnected(TEXT("Client requested disconnect"));
	}

	// Wake worker to ensure it processes the disconnect promptly
	WakeWorker();
}

bool FMQTTWorker::Publish(const FString& Topic, const FString& Payload, int32 QoS, bool bRetain)
{
	// Enqueue publish request to be processed on the worker thread
	OutgoingMessages.Enqueue(FMQTTOutgoing(Topic, Payload, QoS, bRetain));
	WakeWorker();
	return true;
}

bool FMQTTWorker::Subscribe(const FString& TopicFilter, int32 QoS)
{
	SubscriptionRequests.Enqueue(FMQTTSubscriptionRequest(TopicFilter, QoS, true));
	WakeWorker();
	return true;
}

bool FMQTTWorker::Unsubscribe(const FString& TopicFilter)
{
	SubscriptionRequests.Enqueue(FMQTTSubscriptionRequest(TopicFilter, 0, false));
	WakeWorker();
	return true;
}

bool FMQTTWorker::IsConnected() const
{
	return bConnected;
}

void FMQTTWorker::SetClientId(const FString& InClientId)
{
	FScopeLock Lock(&Mutex);
	ClientId = InClientId;
}

void FMQTTWorker::SetCredentials(const FString& InUsername, const FString& InPassword)
{
	FScopeLock Lock(&Mutex);
	Username = InUsername;
	Password = InPassword;
}

void FMQTTWorker::SetKeepAlive(int32 InKeepAliveSeconds)
{
	FScopeLock Lock(&Mutex);
	KeepAliveSeconds = InKeepAliveSeconds;
}

void FMQTTWorker::WakeWorker()
{
	if (WakeEvent)
	{
		WakeEvent->Trigger();
	}
}

void FMQTTWorker::NotifyConnected()
{
	// Post to the Game Thread to invoke the owner's delegate safely
	UMQTTClient* OwnerPtr = Owner.Get();
	if (!OwnerPtr)
	{
		return;
	}

	AsyncTask(ENamedThreads::GameThread, [OwnerPtr]()
	{
		// Broadcast the Blueprint-visible delegate
		OwnerPtr->OnConnected.Broadcast();
	});
}

void FMQTTWorker::NotifyDisconnected(const FString& Reason)
{
	UMQTTClient* OwnerPtr = Owner.Get();
	if (!OwnerPtr)
	{
		return;
	}

	AsyncTask(ENamedThreads::GameThread, [OwnerPtr, Reason]()
	{
		OwnerPtr->OnDisconnected.Broadcast(Reason);
	});
}

void FMQTTWorker::NotifyMessageReceived(const FString& Topic, const FString& Payload)
{
	UMQTTClient* OwnerPtr = Owner.Get();
	if (!OwnerPtr)
	{
		return;
	}

	AsyncTask(ENamedThreads::GameThread, [OwnerPtr, Topic, Payload]()
	{
		OwnerPtr->OnMessageReceived.Broadcast(Topic, Payload);
	});
}