from pathlib import Path
from typing import Union
import subprocess


def play_audio_blocking(path: Union[str, Path]) -> None:
    """Play an audio file and block until it finishes.

    On Raspberry Pi this uses `mpg123` for MP3 playback.
    """
    audio_path = Path(path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    subprocess.run(["mpg123", "-q", str(audio_path)], check=True)
