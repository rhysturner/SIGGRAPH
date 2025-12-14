#pragma once

#include "CoreMinimal.h"
#include "HAL/Runnable.h"
#include "HAL/RunnableThread.h"
#include "Templates/UniquePtr.h"
#include "Containers/Queue.h"
#include "Misc/ScopeLock.h"
#include "HAL/Event.h"
#include "Sockets.h"
#include "SocketSubsystem.h"
#include "IPAddress.h"
#include "MQTTClient.h" // Public header for delegate types and UMQTTClient forward

/**
 * FMQTTWorker
 *
 * A lightweight FRunnable-based worker that owns an MQTT connection and performs network IO on a background thread.
 *
 * Responsibilities:
 * - Establish and maintain a TCP (or TLS) connection to an MQTT broker.
 * - Send outgoing publishes/subscriptions enqueued by the game thread.
 * - Read incoming MQTT packets and forward them to the owning UMQTTClient instance via thread-safe callbacks.
 *
 * Notes:
 * - This header provides the public API and data-members required by the implementation. The heavy lifting
 *   (parsing/serializing MQTT packets, TLS handling or integration with a third-party MQTT library) belongs
 *   in the corresponding .cpp file.
 * - The worker keeps a weak pointer to the UMQTTClient owner to avoid prolonging UObject lifetime from the background thread.
 * - All API methods are safe to call from the game thread.
 */

class UMQTTClient;

/** Simple POD representing an outgoing MQTT message or control request. */
struct FMQTTOutgoing
{
	FString Topic;
	FString Payload;
	int32 QoS;
	bool bRetain;

	FMQTTOutgoing()
		: Topic()
		, Payload()
		, QoS(0)
		, bRetain(false)
	{}

	FMQTTOutgoing(const FString& InTopic, const FString& InPayload, int32 InQoS = 0, bool InRetain = false)
		: Topic(InTopic)
		, Payload(InPayload)
		, QoS(InQoS)
		, bRetain(InRetain)
	{}
};

/** Simple POD representing a subscription/unsubscribe request. */
struct FMQTTSubscriptionRequest
{
	FString TopicFilter;
	int32 QoS;
	bool bSubscribe; // true -> subscribe, false -> unsubscribe

	FMQTTSubscriptionRequest() : TopicFilter(), QoS(0), bSubscribe(true) {}
	FMQTTSubscriptionRequest(const FString& InFilter, int32 InQoS, bool InSubscribe)
		: TopicFilter(InFilter), QoS(InQoS), bSubscribe(InSubscribe) {}
};

/**
 * FMQTTWorker - FRunnable
 */
class FMQTTWorker : public FRunnable
{
public:
	/** Create a worker associated with an owner UObject. The worker will not start its thread until Start() is called. */
	FMQTTWorker(UMQTTClient* InOwner);
	virtual ~FMQTTWorker();

	// FRunnable interface
	virtual bool Init() override;
	virtual uint32 Run() override;
	virtual void Stop() override;
	virtual void Exit() override;

	/** Start the runnable by creating the thread. Safe to call from game thread. */
	bool Start();

	/** Shutdown the runnable and join the thread. Safe to call from game thread. */
	void Shutdown();

	/** Request connect to broker. This enqueues a connect request processed on the worker thread. */
	void Connect(const FString& InHost, int32 InPort, bool bInUseTLS = false);

	/** Request a disconnect. If bForce is true, the worker will immediately drop the socket. */
	void Disconnect(bool bForce = false);

	/** Publish a message (thread-safe; enqueues to outgoing queue). */
	bool Publish(const FString& Topic, const FString& Payload, int32 QoS = 0, bool bRetain = false);

	/** Subscribe to a topic filter. */
	bool Subscribe(const FString& TopicFilter, int32 QoS = 0);

	/** Unsubscribe from a topic filter. */
	bool Unsubscribe(const FString& TopicFilter);

	/** Query whether the worker currently believes the network connection is established. */
	bool IsConnected() const;

	/** Set client identifier and credentials prior to connecting. Thread-safe. */
	void SetClientId(const FString& InClientId);
	void SetCredentials(const FString& InUsername, const FString& InPassword);
	void SetKeepAlive(int32 InKeepAliveSeconds);

private:
	/** Weak pointer to owner UObject; used to forward messages back on the game thread. */
	TWeakObjectPtr<UMQTTClient> Owner;

	/** Thread handling this runnable. */
	FRunnableThread* Thread;

	/** Internal synchronization primitives. */
	mutable FCriticalSection Mutex;
	FEvent* WakeEvent; // used to wake up the worker when new work arrives or to signal shutdown

	/** Outgoing queues (MPSC) */
	TQueue<FMQTTOutgoing, EQueueMode::Mpsc> OutgoingMessages;
	TQueue<FMQTTSubscriptionRequest, EQueueMode::Mpsc> SubscriptionRequests;

	/** Internal connection state */
	FString Host;
	int32 Port;
	bool bUseTLS;
	FString Username;
	FString Password;
	FString ClientId;
	int32 KeepAliveSeconds;

	/** Socket objects (low-level TCP socket). Concrete socket handling belongs in the .cpp file. */
	FSocket* Socket;

	/** Atomic control flags */
	FThreadSafeBool bStopRequested;
	FThreadSafeBool bConnected;
	FThreadSafeBool bShutdownComplete;

	/** Internal helpers used by Run() implemented in .cpp */
	bool EstablishConnection();
	void TeardownConnection(const FString& Reason);
	bool SendPublishPacket(const FMQTTOutgoing& Out);
	bool SendSubscribePacket(const FMQTTSubscriptionRequest& Req);
	bool ProcessNetworkReceive();
	void WakeWorker();

	/** Helpers to forward events to the owner on the game thread. These must only be called from the worker thread. */
	void NotifyConnected();
	void NotifyDisconnected(const FString& Reason);
	void NotifyMessageReceived(const FString& Topic, const FString& Payload);

	/** Non-copyable */
	FMQTTWorker(const FMQTTWorker&) = delete;
	FMQTTWorker& operator=(const FMQTTWorker&) = delete;
};
