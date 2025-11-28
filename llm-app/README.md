# Local Ollama Chat Client

A small Python CLI tool that connects to a local [Ollama](https://ollama.com/) service, sends a prompt plus optional conversation history, and prints the model's reply.

## Prerequisites

- Python 3.10+ (recommended)
- A local Ollama server running (defaults to `http://localhost:11434`)
- At least one model pulled in Ollama (default used here is `llama3.1`)

## Setup

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Usage

The main entrypoint is `app.py`.

Basic usage with just a prompt:

```bash
python app.py --prompt "Explain ray tracing in simple terms."
```

### Using conversation history

You can pass a conversation history as a JSON file. The expected format is a list of message objects:

```json
[
  {"role": "system", "content": "You are a helpful assistant."},
  {"role": "user", "content": "Hi there!"},
  {"role": "assistant", "content": "Hello! How can I help you today?"}
]
```

Save this as `history.json`, then run:

```bash
python app.py \
  --prompt "Can you go into more detail about how path tracing differs?" \
  --history history.json
```

### Command-line options

- `--prompt` (required): Current user prompt to send to the model.
- `--history`: Path to a JSON file with prior messages.
- `--model`: Ollama model name to use (default: `llama3.1`).
- `--base-url`: Base URL of the Ollama server (default: `http://localhost:11434`).

### Example

```bash
python app.py --prompt "List three key differences between rasterization and ray tracing."
```

If the request succeeds, you'll see output like:

```text
Assistant:
<model response here>
```

## Notes

- The script uses the Ollama `/api/chat` endpoint with `stream: false`.
- Conversation history is validated to ensure each message has a valid `role` (`user`, `assistant`, or `system`) and string `content`.

## Troubleshooting

- If you see an HTTP error, check that Ollama is running and reachable at the configured `--base-url`.
- If the history JSON is malformed, the script will print an error describing which item failed validation.