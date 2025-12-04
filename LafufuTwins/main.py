#!/usr/bin/env python3
"""
Virtual Assistant - Main Application
A voice-activated assistant powered by Ollama
"""

import argparse
import sys

from assistant import VirtualAssistant, test_microphone, test_ollama_connection


def main():
    """Main entry point for the virtual assistant application"""
    parser = argparse.ArgumentParser(
        description="Virtual Assistant powered by Ollama and speech recognition"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="llama2",
        help="Ollama model to use (default: llama2)",
    )
    parser.add_argument(
        "--test-mic",
        action="store_true",
        help="Test microphone and list available devices",
    )
    parser.add_argument(
        "--test-ollama", action="store_true", help="Test Ollama connection"
    )
    parser.add_argument(
        "--test-all", action="store_true", help="Run all tests before starting"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🤖 Virtual Assistant - Powered by Ollama")
    print("=" * 60)

    # Run tests if requested
    if args.test_mic or args.test_all:
        print("\n--- Microphone Test ---")
        if not test_microphone():
            print("\n⚠️  Microphone test failed!")
            if not args.test_all:
                sys.exit(1)
        print()

    if args.test_ollama or args.test_all:
        print("\n--- Ollama Test ---")
        if not test_ollama_connection(args.model):
            print("\n⚠️  Ollama test failed!")
            print("Please ensure:")
            print("  1. Ollama is installed (https://ollama.ai)")
            print("  2. Ollama is running (run 'ollama serve')")
            print(f"  3. Model is installed (run 'ollama pull {args.model}')")
            if not args.test_all:
                sys.exit(1)
        print()

    # If only running tests, exit
    if args.test_mic or args.test_ollama or args.test_all:
        print("=" * 60)
        print("Tests complete!")
        print("=" * 60)
        if args.test_mic or args.test_ollama:
            return

    # Create and run the assistant
    print("\n🚀 Starting Virtual Assistant...")
    print(f"Using model: {args.model}")
    print("\nCommands:")
    print("  - Say 'exit', 'quit', or 'goodbye' to stop")
    print("  - Say 'clear history' to reset the conversation")
    print("  - Press Ctrl+C to interrupt\n")
    print("=" * 60)

    try:
        assistant = VirtualAssistant(model_name=args.model)
        assistant.run()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Thank you for using Virtual Assistant!")
    print("=" * 60)


if __name__ == "__main__":
    main()
