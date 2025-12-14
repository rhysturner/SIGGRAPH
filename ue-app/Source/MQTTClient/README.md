# MQTTClient (UE5.7) — README

This module provides a minimal, Blueprint-friendly MQTT client for Unreal Engine 5.7. It includes:
- `UMQTTClient` — a `UObject` wrapper exposing Connect / Disconnect / Publish / Subscribe APIs to Blueprints and C++.
- `FMQTTWorker` — a background `FRunnable` worker that processes network operations off the game thread.
- A non-invasive `Build.cs` that supports optionally linking third-party MQTT libraries (mosquitto / paho) when provided.

This module is intended as a starting point: it compiles and runs with an internal stub worker (no real MQTT wire-protocol implemented). You can integrate a real MQTT library and toggle the behavior with the compile-time macro provided in the module.

Why use this
- Provides a simple, engine-native entry point for adding MQTT messaging to gameplay logic and Blueprints.
- Separates game-thread-facing API (UObject) from networking background worker (FRunnable).
- Includes scaffolding for integrating third-party MQTT libraries when you want production-grade MQTT.

Contents
- `Source/MQTTClient/MQTTClient.Build.cs` — module rules and optional third-party detection.
- `Source/MQTTClient/Public/MQTTClient.h` — public `UMQTTClient` declaration and Blueprint delegates.
- `Source/MQTTClient/Private/MQTTClient.cpp` — `UMQTTClient` implementation and minimal PIMPL usage.
- `Source/MQTTClient/Private/MQTTClientWorker.h` — worker declaration (FRunnable).
- `Source/MQTTClient/README.md` — this file.

Public API quick reference
- `UMQTTClient` (BlueprintType):
  - `Connect(const FString& BrokerAddress, int32 BrokerPort = 1883, bool bUseTLS = false) -> bool`
  - `Disconnect(bool bForce = false)`
  - `Publish(const FString& Topic, const FString& Payload, int32 QoS = 0, bool bRetain = false) -> bool`
  - `Subscribe(const FString& TopicFilter, int32 QoS = 0) -> bool`
  - `Unsubscribe(const FString& TopicFilter) -> bool`
  - `SetCredentials(const FString& Username, const FString& Password)`
  - `SetClientId(const FString& ClientId)`
  - `SetKeepAlive(int32 KeepAliveSeconds)`
  - Delegates:
    - `OnConnected` — fired when connection established
    - `OnDisconnected` — fired when disconnected (reason string)
    - `OnMessageReceived(Topic, Payload)` — fired when a message arrives for subscribed topic(s)

Example: C++ usage
Use `UMQTTClient` from C++ by including the public header and creating/using the object. Example snippet:

```ue-app/Source/MQTTClient/Public/MQTTClient.h#L1-200
// Example (pseudo) usage:
//
// #include "MQTTClient.h"
//
// void MyFunction()
// {
//     UMQTTClient* Client = NewObject<UMQTTClient>();
//     Client->SetClientId(TEXT("MyUEClient"));
//     Client->SetCredentials(TEXT("user"), TEXT("pass"));
//     Client->OnConnected.AddDynamic(this, &MyClass::OnMqttConnected);
//     Client->OnMessageReceived.AddDynamic(this, &MyClass::OnMqttMessage);
//     Client->Connect(TEXT("broker.hivemq.com"), 1883, false);
//     Client->Subscribe(TEXT("my/game/topic"));
//     Client->Publish(TEXT("my/game/topic"), TEXT("hello from UE"));
// }
```

Blueprint usage
- Create a variable of type `MQTTClient` (expose `UMQTTClient` by creating an instance with `Construct Object from Class` or `New Object` in graph).
- Call `SetClientId` / `SetCredentials` if required.
- Call `Connect` — hook `OnConnected` to be notified when connection established.
- Call `Subscribe` and hook `OnMessageReceived`.
- Call `Publish` to send messages.

Build / Integration notes
- The module includes a `Build.cs` which attempts to detect and link third-party MQTT libraries if placed under a `ThirdParty` folder adjacent to the module. The build-time macro `WITH_MQTT_THIRD_PARTY` is added automatically by the `Build.cs` when such libraries are found. You can therefore implement real MQTT behavior conditionally in C++ using this macro.
- The `MQTTClient` module's `Build.cs` already pulls in `Sockets` and `Networking` as UE dependencies.

If you plan to add a third-party MQTT library:
1. Place the library headers/libs under `ThirdParty/mosquitto` or `ThirdParty/paho` near the project or module (see `Build.cs` behavior).
2. Extend `FMQTTWorker` implementation in `MQTTClientWorker` to initialize and use the chosen library's client API for connect/publish/subscribe/receive.
3. Ensure thread-safety and route callbacks to the game thread using `AsyncTask(ENamedThreads::GameThread, ...)` when dispatching delegates.

Where the stubs live
- The current worker is a stub that logs actions and echoes publishes back to `OnMessageReceived`. Replace the stubbed logic in:
  - `ue-app/Source/MQTTClient/Private/MQTTClient.cpp`
  - `ue-app/Source/MQTTClient/Private/MQTTClientWorker.h` and its corresponding implementation file content.
- The public interface is defined in:
  - `ue-app/Source/MQTTClient/Public/MQTTClient.h`

Example: where to update worker implementation
The `FMQTTWorker` class is defined in the private header. Replace stub internals (establish/connect/send/receive/parse) with a proper implementation or wrap a third-party client. The worker must:
- perform network IO on its thread
- notify `UMQTTClient` on the Game Thread (do not touch UObjects directly from worker thread)
- gracefully shutdown before the UObject is destroyed (see `BeginDestroy`).

Threading & lifetime considerations
- `UMQTTClient::BeginDestroy` shuts down and joins the worker thread. Always make sure the worker is stopped before the UObject is destroyed — the code does that for you in the current implementation.
- All delegate broadcasts are performed on the Game Thread (via `AsyncTask`) to make them safe for Blueprint/UE usage.

Extending for TLS / Authentication / Persistence
- TLS: integrate a TLS-capable MQTT client or use platform TLS APIs before socket connection. TLS is not implemented in the stub.
- Authentication: `SetCredentials` is present to pass username/password to the worker; an actual client must use those values when connecting.
- Persistence / QoS 1/2: implement message persistence and confirmation flows per MQTT spec.

Build macros and export symbol
- The build module defines `WITH_MQTT_THIRD_PARTY=1` when a third-party lib is found; use `#if WITH_MQTT_THIRD_PARTY` around code that depends on the library.
- An API export macro `MQTTCLIENT_API` is available for cross-module symbol visibility via `MQTTClientModule.h`.

Limitations / TODO (recommended)
- The provided implementation is a functional scaffold but only includes a stub worker (no MQTT wire-protocol).
- Implement full MQTT packet parsing/serialization or wrap a robust library (mosquitto, paho).
- Add robust error handling, automatic reconnect/backoff, TLS support, keep-alive/ping handling, and QoS 1/2 flows with message persistence.
- Add unit/integration tests for the network layer.

License
- This repository does not include third-party MQTT libraries by default. Any third-party library you add must be licensed appropriately.
- You may place your chosen license text here (e.g., MIT or your project license).

Contact / Next steps
- If you want, I can:
  - Integrate an MQTT C library (paho or mosquitto) into this module and wire the worker to it.
  - Implement full MQTT publish/subscribe + receive parsing.
  - Add TLS support and packaging rules for runtime DLLs.
Tell me which direction you want (wrap `mosquitto`, wrap `paho`, or implement a pure-C++ MQTT serializer/parser), and I will provide the next changes or instructions.

Relevant files for implementation
- `ue-app/Source/MQTTClient/MQTTClient.Build.cs`
- `ue-app/Source/MQTTClient/Public/MQTTClient.h`
- `ue-app/Source/MQTTClient/Private/MQTTClient.cpp`
- `ue-app/Source/MQTTClient/Private/MQTTClientWorker.h`
