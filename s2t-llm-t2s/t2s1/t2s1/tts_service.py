from pathlib import Path
from typing import Union
from io import BytesIO

from gtts import gTTS


def _validate_text(text: str) -> str:
    text = (text or "").strip()
    if not text:
        raise ValueError("No text provided for text-to-speech.")
    return text


def synthesize_to_file(
    text: str,
    output_path: Union[str, Path],
    lang: str = "en",
) -> Path:
    """Convert text to speech and save as an MP3 file.

    Returns the Path to the written file.
    """
    text = _validate_text(text)
    output_path = Path(output_path)

    tts = gTTS(text=text, lang=lang)
    tts.save(str(output_path))
    return output_path


def synthesize_to_bytes(
    text: str,
    lang: str = "en",
) -> bytes:
    """Convert text to speech and return raw MP3 bytes."""
    text = _validate_text(text)

    buf = BytesIO()
    tts = gTTS(text=text, lang=lang)
    tts.write_to_fp(buf)
    return buf.getvalue()
