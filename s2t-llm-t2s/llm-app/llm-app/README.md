# Local Ollama Chat Client

A small Python CLI tool that connects to a local [Ollama](https://ollama.com/) service, sends a prompt plus optional conversation history, and prints the model's reply.

## Prerequisites

- Python 3.10+ (recommended)
- A local Ollama server running (defaults to `http://localhost:11434`)
- At least one model pulled in Ollama (default used here is `deepseek-r1:7b`)

## Setup

Install Python dependencies:

```bash
pip install -r requirements.txt
```

The only required dependency is:
- `requests>=2.31.0`

## Usage

The main entrypoint is `app.py`.

### Basic usage with just a prompt:

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
- `--model`: Ollama model name to use (default: `deepseek-r1:7b`).
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

## Implementation Details

### Architecture

The `OllamaClient` class provides a minimal interface to the Ollama HTTP API:
- Uses the `/api/chat` endpoint with `stream: false` for non-streaming responses
- Automatically combines conversation history with the current prompt
- Validates message format and roles

### Message Format

Each message in the conversation history must have:
- `role`: One of `"user"`, `"assistant"`, or `"system"`
- `content`: A string containing the message text

The current prompt is always appended as the final user message before sending to Ollama.

### Error Handling

The script validates:
- JSON file structure (must be a list)
- Message format (must be objects with `role` and `content`)
- Valid role values
- HTTP connectivity to Ollama server

## Notes

- The script uses the Ollama `/api/chat` endpoint with `stream: false`.
- Conversation history is validated to ensure each message has a valid `role` (`user`, `assistant`, or `system`) and string `content`.
- The request payload is printed to stdout for debugging purposes.

## Troubleshooting

- **HTTP error**: Check that Ollama is running and reachable at the configured `--base-url`. You can verify by visiting `http://localhost:11434` in your browser or running `ollama list` in a terminal.
- **Model not found**: Ensure the specified model (default: `deepseek-r1:7b`) is pulled in Ollama. Run `ollama pull deepseek-r1:7b` to download it.
- **History JSON errors**: The script will print an error describing which item failed validation. Common issues:
  - File is not valid JSON
  - Messages are not in a list format
  - Missing `role` or `content` fields
  - Invalid `role` value (must be `user`, `assistant`, or `system`)

## Example Workflow

1. Start Ollama server (if not already running):
   ```bash
   ollama serve
   ```

2. Pull a model (if not already available):
   ```bash
   ollama pull deepseek-r1:7b
   ```

3. Run the chat client:
   ```bash
   python app.py --prompt "Hello, how are you?"
   ```

4. Use with conversation history:
   ```bash
   # Create history.json with previous conversation
   python app.py --prompt "What did we talk about?" --history history.json
   ```
