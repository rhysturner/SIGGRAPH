#!/usr/bin/env python3
"""Simple Python client for a local Ollama service.

This script:
- Reads a user prompt from the CLI
- Optionally reads a conversation history from a JSON file
- Sends both to a local Ollama server via its HTTP API
- Prints the model's reply

Usage examples:
  python app.py --prompt "Hello" 
  python app.py --prompt "Continue the story" --history history.json

Where `history.json` looks like:
[
  {"role": "user", "content": "Hi"},
  {"role": "assistant", "content": "Hello! How can I help you today?"}
]
"""

import argparse
import json
from dataclasses import dataclass
from typing import Generator, List, Literal, TypedDict

import requests


Role = Literal["user", "assistant", "system"]


@dataclass
class Message:
    role: Role
    content: str


class OllamaChatResponseMessage(TypedDict):
    role: Role
    content: str


class OllamaChatResponse(TypedDict, total=False):
    model: str
    created_at: str
    message: OllamaChatResponseMessage
    done: bool


class OllamaChatStreamChunk(TypedDict, total=False):
    """Single streamed chunk from Ollama `/api/chat` with stream=true."""

    model: str
    created_at: str
    message: OllamaChatResponseMessage
    done: bool


class OllamaClient:
    """Minimal client for the local Ollama HTTP API using `/api/chat`."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "deepseek-r1:7b") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(self, prompt: str, history: List[Message] | None = None) -> str:
        """Send a non-streaming chat request to Ollama via `/api/chat`.

        :param prompt: The current user message.
        :param history: Optional list of prior messages.
        :return: Assistant reply content.
        """
        messages_payload: list[dict[str, str]] = []

        if history:
            for m in history:
                messages_payload.append({"role": m.role, "content": m.content})

        # Current user prompt is always the last message
        messages_payload.append({"role": "user", "content": prompt})

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages_payload,
            "stream": False,
        }

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()

        data: OllamaChatResponse = response.json()
        message = data.get("message")
        if not message:
            raise RuntimeError(f"Unexpected response shape from Ollama: {data}")

        return message["content"]

    def chat_stream(self, prompt: str, history: List[Message] | None = None) -> Generator[str, None, None]:
        """Stream a chat response from Ollama, yielding text chunks as they arrive.

        This uses `/api/chat` with ``stream=true`` and yields each non-empty
        ``message.content`` piece so callers can render incrementally.
        """
        messages_payload: list[dict[str, str]] = []

        if history:
            for m in history:
                messages_payload.append({"role": m.role, "content": m.content})

        messages_payload.append({"role": "user", "content": prompt})

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages_payload,
            "stream": True,
        }

        # Debug: print the exact JSON payload we send to the LLM
        print("Payload to Ollama:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))

        with requests.post(url, json=payload, stream=True, timeout=120) as response:
            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue

                try:
                    data: OllamaChatStreamChunk = json.loads(line)
                except json.JSONDecodeError:
                    continue

                message = data.get("message")
                if not message:
                    continue

                chunk = message.get("content") or ""
                if chunk:
                    yield chunk

                if data.get("done"):
                    break


def load_history_from_json(path: str) -> List[Message]:
    """Load conversation history from a JSON file.

    Expected format: list of {"role": "user"|"assistant"|"system", "content": "..."}.
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        raise ValueError("History JSON must be a list of messages")

    history: List[Message] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"History item at index {i} is not an object: {item!r}")
        role = item.get("role")
        content = item.get("content")
        if role not in ("user", "assistant", "system"):
            raise ValueError(f"Invalid role at index {i}: {role!r}")
        if not isinstance(content, str):
            raise ValueError(f"Invalid content at index {i}: {content!r}")
        history.append(Message(role=role, content=content))

    return history


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chat with a local Ollama model using a prompt and conversation history.")
    parser.add_argument("--prompt", required=True, help="Current user prompt to send to the model.")
    parser.add_argument(
        "--history",
        help="Path to JSON file containing conversation history (list of {role, content}).",
    )
    parser.add_argument(
        "--model",
        default="deepseek-r1:7b",
        help="Ollama model name to use (default: %(default)s).",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:11434",
        help="Base URL of the Ollama server (default: %(default)s).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    history: List[Message] | None = None
    if args.history:
        history = load_history_from_json(args.history)

    client = OllamaClient(base_url=args.base_url, model=args.model)
    try:
        reply = client.chat(prompt=args.prompt, history=history)
    except requests.RequestException as e:
        print(f"HTTP error talking to Ollama: {e}")
        raise SystemExit(1)
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}")
        raise SystemExit(1)

    print("Assistant:")
    print(reply)


if __name__ == "__main__":
    main()
