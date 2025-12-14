#pragma once

#include "CoreMinimal.h"
#include "MQTTClientModule.h"
#include "UObject/NoExportTypes.h"
#include "MQTTClient.generated.h"

/**
 * MQTT client for Unreal Engine 5.7
 *
 * - Provides a Blueprint-friendly UObject wrapper for basic MQTT operations:
 *   Connect, Disconnect, Publish, Subscribe, Unsubscribe.
 * - Exposes events (delegates) for connected, disconnected and message received.
 * - Designed to be implementation-agnostic: if a third-party MQTT library is linked (see WITH_MQTT_THIRD_PARTY),
 *   the module can use it; otherwise the class provides the interface and basic stubs that can be implemented.
 *
 * Notes:
 * - This header only defines the interface. Implementation details should live in the corresponding .cpp file.
 * - For production usage you will want to add thread-safety, reconnection logic, TLS support and proper error handling.
 */

// Event when client successfully connects (no parameters)
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FMQTTEventConnected);

// Event when client disconnects (optionally with reason)
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMQTTEventDisconnected, const FString&, Reason);

// Event when a message is received: Topic and Payload (both UTF-8 / FString)
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMQTTEventMessageReceived, const FString&, Topic, const FString&, Payload);

/**
 * UMQTTClient
 *
 * Blueprintable UObject that encapsulates an MQTT client.
 */
UCLASS(BlueprintType, Blueprintable)
class MQTTCLIENT_API UMQTTClient : public UObject
{
    GENERATED_BODY()

public:
    UMQTTClient();

    // --- Blueprint-exposed API ---

    /**
     * Connect to an MQTT broker.
     *
     * @param BrokerAddress - Hostname or IP of the broker (e.g. \"broker.hivemq.com\")
     * @param BrokerPort - Port number (usual 1883 for plaintext, 8883 for TLS)
     * @param bUseTLS - Whether to use TLS for the connection (implementation-dependent)
     * @return true if the connection attempt was started successfully (not necessarily connected immediately)
     */
    UFUNCTION(BlueprintCallable, Category = \"MQTT|Connection\")
    bool Connect(const FString& BrokerAddress, int32 BrokerPort = 1883, bool bUseTLS = false);

    /**
     * Disconnect from the MQTT broker.
     *
     * @param bForce - If true, force immediate disconnect; otherwise perform a graceful disconnect if supported.
     */
    UFUNCTION(BlueprintCallable, Category = \"MQTT|Connection\")
    void Disconnect(bool bForce = false);

    /**
     * Publish a message to a topic.
     *
     * @param Topic - Topic to publish to.
     * @param Payload - Message payload (string). If you need binary support, provide encoding externally.
     * @param QoS - Quality of Service (0,1,2). Implementation may clamp unsupported values.
     * @param bRetain - Whether the broker should retain this message.
     * @return true if the publish request was accepted locally.
     */
    UFUNCTION(BlueprintCallable, Category = \"MQTT|Messaging\")
    bool Publish(const FString& Topic, const FString& Payload, int32 QoS = 0, bool bRetain = false);

    /**
     * Subscribe to a topic filter.
     *
     * @param TopicFilter - Topic filter to subscribe to (supports wildcards as broker supports).
     * @param QoS - Requested QoS level for the subscription.
     * @return true if the subscribe request was accepted locally.
     */
    UFUNCTION(BlueprintCallable, Category = \"MQTT|Messaging\")
    bool Subscribe(const FString& TopicFilter, int32 QoS = 0);

    /**
     * Unsubscribe from a topic filter.
     *
     * @param TopicFilter - Topic filter to unsubscribe from.
     * @return true if the unsubscribe request was accepted locally.
     */
    UFUNCTION(BlueprintCallable, Category = \"MQTT|Messaging\")
    bool Unsubscribe(const FString& TopicFilter);

    /**
     * Set credentials for authentication (username/password).
     * Some brokers require this before connecting.
     */
    UFUNCTION(BlueprintCallable, Category = \"MQTT|Connection\")
    void SetCredentials(const FString& Username, const FString& Password);

    /**
     * Set a client identifier to use when connecting. If empty, an implementation-specific client id may be generated.
     */
    UFUNCTION(BlueprintCallable, Category = \"MQTT|Connection\")
    void SetClientId(const FString& ClientId);

    /**
     * Check whether this client believes it is connected.
     */
    UFUNCTION(BlueprintCallable, Category = \"MQTT|Connection\")
    bool IsConnected() const;

    /**
     * Set keep-alive interval in seconds (0 to disable). Set before connecting.
     */
    UFUNCTION(BlueprintCallable, Category = \"MQTT|Connection\")
    void SetKeepAlive(int32 KeepAliveSeconds);

    // --- Delegates / Events ---

    // Called when the client successfully connects (or when a connection is established).
    UPROPERTY(BlueprintAssignable, Category = \"MQTT|Events\")
    FMQTTEventConnected OnConnected;

    // Called when the client disconnects; reason may be empty.
    UPROPERTY(BlueprintAssignable, Category = \"MQTT|Events\")
    FMQTTEventDisconnected OnDisconnected;

    // Called when a message is received which matches a subscription.
    UPROPERTY(BlueprintAssignable, Category = \"MQTT|Events\")
    FMQTTEventMessageReceived OnMessageReceived;

protected:
    // Internal implementation details should be in the .cpp and in platform-specific/private code.
    // Example: a pointer to a PIMPL struct or a third-party client wrapper.
    // Forward-declare a private implementation struct to hide implementation details from consumers.
    struct FImpl;
    TUniquePtr<FImpl> Impl;

    // Configuration state
    UPROPERTY()
    FString Broker;

    UPROPERTY()
    int32 Port;

    UPROPERTY()
    bool bUseTLS;

    UPROPERTY()
    FString Username;

    UPROPERTY()
    FString Password;

    UPROPERTY()
    FString ClientId;

    UPROPERTY()
    int32 KeepAliveSeconds;

    UPROPERTY()
    bool bConnected;

    // Helper internal signaling functions (not exposed to Blueprint)
    void BroadcastConnected();
    void BroadcastDisconnected(const FString& Reason);
    void BroadcastMessageReceived(const FString& Topic, const FString& Payload);

public:
    // Virtual destructor to allow derived/test classes to clean up
    virtual void BeginDestroy() override;
};

#ifdef WITH_MQTT_THIRD_PARTY
// If a third-party library is available, the implementation in the .cpp can include headers conditionally
// and implement the FImpl to use that library. The macro is defined by the module's Build.cs when libraries are found.
#endif // WITH_MQTT_THIRD_PARTY