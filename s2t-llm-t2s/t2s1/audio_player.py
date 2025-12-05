from __future__ import annotations

from pathlib import Path
from typing import Iterable, Union
import os
import shutil
import subprocess


# Default players commonly available on Raspberry Pi / Debian systems that
# can handle MP3 output from gTTS. Ordered by preference.
_DEFAULT_PLAYERS: tuple[str, ...] = (
    "omxplayer",  # classic Raspberry Pi player (may not exist on newer OSes)
    "aplay",      # ALSA CLI player (WAV/PCM), good for direct device output
    "cvlc",       # VLC console (no GUI, suitable for headless systems)
    "vlc",        # full VLC, falls back to GUI if no console variant
    "ffplay",     # from ffmpeg
    "mpg123",     # lightweight CLI MP3 player
)


def _resolve_player(candidates: Iterable[str]) -> str:
    """Return the first available player from *candidates*.

    Respects the AUDIO_PLAYER environment variable if set, otherwise falls
    back to the default candidate list.
    """

    # 1. Explicit override via env var
    override = os.environ.get("AUDIO_PLAYER")
    if override:
        player = shutil.which(override)
        if player is None:
            raise RuntimeError(
                "AUDIO_PLAYER is set to '%s' but that executable was not found in PATH" % override
            )
        return player

    # 2. First available from candidates
    for name in candidates:
        player = shutil.which(name)
        if player is not None:
            return player

    raise RuntimeError(
        "No suitable audio player found. Tried: %s. "
        "Install one of these (e.g. 'sudo apt-get install vlc' or 'sudo apt-get install mpg123') "
        "or set the AUDIO_PLAYER environment variable to a compatible player."
        % ", ".join(candidates)
    )


def play_audio_blocking(path: Union[str, Path]) -> None:
    """Play an audio file and block until it finishes.

    Designed for Raspberry Pi, but works on any system with a supported
    command-line player in PATH.

    Selection order by default: omxplayer -> aplay -> cvlc -> vlc -> ffplay -> mpg123.

    You can force a specific player by setting the AUDIO_PLAYER environment
    variable, e.g. `AUDIO_PLAYER=aplay` to use ALSA directly or `AUDIO_PLAYER=cvlc` for headless VLC.
    """

    audio_path = Path(path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    player = _resolve_player(_DEFAULT_PLAYERS)

    # If we're using aplay but the source is MP3, convert to WAV first via ffmpeg.
    name = Path(player).name
    if name == "aplay" and audio_path.suffix.lower() != ".wav":
        wav_path = audio_path.with_suffix(".wav")
        # Convert MP3 -> WAV using ffmpeg; overwrite existing WAV if present.
        conv_cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(audio_path), str(wav_path)]
        subprocess.run(conv_cmd, check=True)
        audio_path = wav_path

    # Some players (e.g. omxplayer, vlc) don't need extra flags; others like
    # mpg123 prefer quiet mode. For portability, start with just the path; if
    # you need player-specific flags later, extend this function accordingly.
    cmd = [player, str(audio_path)]

    # Special-case mpg123 to keep it quiet (previous behavior).
    if name == "mpg123":
        cmd.insert(1, "-q")

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        # Should not happen because we already resolved the player with which(),
        # but keep the message clear if PATH/env change between checks.
        raise RuntimeError(
            f"Failed to execute audio player '{player}' for playback."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Audio player '{player}' exited with status {exc.returncode} "
            f"while playing {audio_path!s}"
        ) from exc
