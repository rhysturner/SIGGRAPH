using System;
using System.IO;
using UnrealBuildTool;

public class MQTTClient : ModuleRules
{
    public MQTTClient(ReadOnlyTargetRules Target) : base(Target)
    {
        // Use explicit/shared PCHs for faster compile
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        // Enable exceptions for some MQTT C++ libs if needed
        bEnableExceptions = true;

        // C++ standard (UE5.7 supports C++17/C++20 depending on engine settings; choose C++17 which is widely compatible)
        CppStandard = CppStandardVersion.Cpp17;

        // Public include directories for this module
        PublicIncludePaths.Add(Path.Combine(ModuleDirectory, "Public"));

        // Private include directories for this module
        PrivateIncludePaths.Add(Path.Combine(ModuleDirectory, "Private"));

        // Core engine dependencies
        PublicDependencyModuleNames.AddRange(new string[] {
            "Core",
            "CoreUObject",
            "Engine",
            "Sockets",      // for low-level socket usage if needed by MQTT implementation
            "Networking"    // networking helpers
        });

        // Modules only used internally
        PrivateDependencyModuleNames.AddRange(new string[] {
            "Projects"
        });

        // Optionally allow using a third-party MQTT implementation placed under Source/<Module>/ThirdParty or <ProjectRoot>/ThirdParty
        string ModulePath = ModuleDirectory;
        string ThirdPartyPath = Path.GetFullPath(Path.Combine(ModulePath, "..", "..", "ThirdParty"));

        // Attempt to load a mosquitto/paho library if present. If not found, the module will still compile,
        // but compile-time macro WITH_MQTT_THIRD_PARTY will be 0 and the plugin/module can fall back to a pure-UE implementation or stub.
        bool bFoundThirdParty = false;

        if (Directory.Exists(ThirdPartyPath))
        {
            // Check for common third-party library folders. This is a best-effort loader and can be extended.
            // mosquitto
            string MosquittoPath = Path.Combine(ThirdPartyPath, "mosquitto");
            if (Directory.Exists(MosquittoPath))
            {
                string IncludePath = Path.Combine(MosquittoPath, "include");
                PublicIncludePaths.Add(IncludePath);

                // Platform-specific library linking
                if (Target.Platform == UnrealTargetPlatform.Win64 || Target.Platform == UnrealTargetPlatform.Win32)
                {
                    string PlatformFolder = Target.Platform == UnrealTargetPlatform.Win64 ? "Win64" : "Win32";
                    string LibPath = Path.Combine(MosquittoPath, "lib", PlatformFolder, "mosquitto.lib");
                    if (File.Exists(LibPath))
                    {
                        PublicAdditionalLibraries.Add(LibPath);
                        bFoundThirdParty = true;
                    }

                    // mosquitto often depends on ws2_32 on Windows
                    PublicSystemLibraries.Add("ws2_32.lib");
                }
                else if (Target.Platform == UnrealTargetPlatform.Linux)
                {
                    // static or shared library names vary; try common names
                    string StaticLib = Path.Combine(MosquittoPath, "lib", "linux", "libmosquitto.a");
                    string SharedLib = "/usr/lib/libmosquitto.so";
                    if (File.Exists(StaticLib))
                    {
                        PublicAdditionalLibraries.Add(StaticLib);
                        bFoundThirdParty = true;
                    }
                    else if (File.Exists(SharedLib))
                    {
                        PublicSystemLibraries.Add(SharedLib);
                        bFoundThirdParty = true;
                    }

                    // Common system libs mosquitto may need
                    PublicSystemLibraries.Add("pthread");
                    PublicSystemLibraries.Add("dl");
                }
                else if (Target.Platform == UnrealTargetPlatform.Mac)
                {
                    string StaticLib = Path.Combine(MosquittoPath, "lib", "mac", "libmosquitto.a");
                    string Dylib = Path.Combine(MosquittoPath, "lib", "mac", "libmosquitto.dylib");
                    if (File.Exists(StaticLib))
                    {
                        PublicAdditionalLibraries.Add(StaticLib);
                        bFoundThirdParty = true;
                    }
                    else if (File.Exists(Dylib))
                    {
                        PublicAdditionalLibraries.Add(Dylib);
                        bFoundThirdParty = true;
                    }

                    // On mac, link system frameworks if needed (add here if you bundle libs that require them)
                }
            }

            // paho.mqtt.c or paho.mqtt.cpp could be placed under ThirdParty/paho
            string PahoPath = Path.Combine(ThirdPartyPath, "paho");
            if (!bFoundThirdParty && Directory.Exists(PahoPath))
            {
                string IncludePath = Path.Combine(PahoPath, "include");
                PublicIncludePaths.Add(IncludePath);

                if (Target.Platform == UnrealTargetPlatform.Win64 || Target.Platform == UnrealTargetPlatform.Win32)
                {
                    string PlatformFolder = Target.Platform == UnrealTargetPlatform.Win64 ? "Win64" : "Win32";
                    string LibPath = Path.Combine(PahoPath, "lib", PlatformFolder, "paho-mqtt3a.lib");
                    if (File.Exists(LibPath))
                    {
                        PublicAdditionalLibraries.Add(LibPath);
                        bFoundThirdParty = true;
                    }
                }
                else if (Target.Platform == UnrealTargetPlatform.Linux)
                {
                    string StaticLib = Path.Combine(PahoPath, "lib", "linux", "libpaho-mqtt3a.a");
                    string SharedLib = "/usr/lib/libpaho-mqtt3a.so";
                    if (File.Exists(StaticLib))
                    {
                        PublicAdditionalLibraries.Add(StaticLib);
                        bFoundThirdParty = true;
                    }
                    else if (File.Exists(SharedLib))
                    {
                        PublicSystemLibraries.Add(SharedLib);
                        bFoundThirdParty = true;
                    }

                    PublicSystemLibraries.Add("pthread");
                    PublicSystemLibraries.Add("dl");
                }
                else if (Target.Platform == UnrealTargetPlatform.Mac)
                {
                    string StaticLib = Path.Combine(PahoPath, "lib", "mac", "libpaho-mqtt3a.a");
                    string Dylib = Path.Combine(PahoPath, "lib", "mac", "libpaho-mqtt3a.dylib");
                    if (File.Exists(StaticLib))
                    {
                        PublicAdditionalLibraries.Add(StaticLib);
                        bFoundThirdParty = true;
                    }
                    else if (File.Exists(Dylib))
                    {
                        PublicAdditionalLibraries.Add(Dylib);
                        bFoundThirdParty = true;
                    }
                }
            }
        }

        // Define a compile-time macro so C++ code can compile conditionally based on availability of third-party libs.
        // Also define module export symbol for the MQTTCLIENT module so public headers can use MQTTCLIENT_API
        PublicDefinitions.Add("MQTTCLIENT_EXPORTS=1");
        PublicDefinitions.Add(string.Format("WITH_MQTT_THIRD_PARTY={0}", bFoundThirdParty ? 1 : 0));

        // If you want to optionally expose a module feature toggle to the editor/project build, add here:
        // PublicDefinitions.Add("MQTT_CLIENT_ENABLE_FEATURE_X=1");

        // Additional settings for packaging: if you bundle dynamic libraries, mark them for delay load or runtime dependencies
        // Example: if you include a .dll in ThirdParty/<lib>/lib/Win64, you might add:
        // RuntimeDependencies.Add(Path.Combine(ThirdPartyPath, "mosquitto", "lib", "Win64", "mosquitto.dll"));

        // Notes:
        // - This Build.cs file intentionally tries to be non-intrusive: the module will compile even if no third-party library is present.
        //   Placeholders (macros) let the C++ implementation decide whether to use a bundled/native MQTT library or fallback to a UE-native implementation.
        // - If you plan to vendor a specific MQTT library, extend the above checks with the exact layout you choose and add RuntimeDependencies for DLLs/dylibs.
    }
}
