#pragma once

// MQTTClientModule.h
//
// Module-level header that defines the export macro `MQTTCLIENT_API` for the MQTTClient module
// and declares the module's logging category.
//
// Usage:
// - When building the MQTTClient module, the build system should define `MQTTCLIENT_EXPORTS`
//   (for example by adding a PublicDefinition in the module's Build.cs). When that symbol is
//   present the API macro will export symbols; otherwise it will import them (on supported platforms).
//
// - This header is intentionally small and safe to include from public headers across the module.

#include "Logging/LogMacros.h"

//
// Define MQTTCLIENT_API
//
// Convention:
// - The build system (e.g. the module's Build.cs) can define `MQTTCLIENT_EXPORTS` when compiling
//   the module itself. This header will then expand `MQTTCLIENT_API` to the appropriate symbol
//   export on each platform. When other modules include this header, `MQTTCLIENT_API` becomes an
//   import declaration on Windows and a default-visibility marker on platforms that support it.
// - If you prefer different naming for the export symbol, adapt the Build.cs definitions accordingly.
//

#ifndef MQTTCLIENT_API
	// Windows (MSVC / clang-cl)
	#if defined(_WIN32) || defined(_WIN64)
		#if defined(MQTTCLIENT_EXPORTS)
			#define MQTTCLIENT_API __declspec(dllexport)
		#else
			#define MQTTCLIENT_API __declspec(dllimport)
		#endif

	// Unix-like platforms (GCC / Clang)
	#elif defined(__GNUC__) || defined(__clang__)
		#if defined(MQTTCLIENT_EXPORTS)
			#define MQTTCLIENT_API __attribute__((visibility("default")))
		#else
			#define MQTTCLIENT_API
		#endif

	// Fallback: no special attributes
	#else
		#define MQTTCLIENT_API
	#endif
#endif // MQTTCLIENT_API

// Logging category for the MQTTClient module.
// Define the category in a single translation unit (typically the module .cpp) with:
//   DEFINE_LOG_CATEGORY(LogMQTTClient);
DECLARE_LOG_CATEGORY_EXTERN(LogMQTTClient, Log, All);

