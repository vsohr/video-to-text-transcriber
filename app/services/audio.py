"""Audio extraction service using FFmpeg."""

import asyncio
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from app.core.config import settings


class FFmpegNotFoundError(Exception):
    """Raised when FFmpeg is not installed or not found."""

    pass


class AudioExtractionError(Exception):
    """Raised when audio extraction fails."""

    pass


def find_ffmpeg() -> Optional[Path]:
    """Find FFmpeg executable in system PATH."""
    ffmpeg_path = shutil.which("ffmpeg")
    return Path(ffmpeg_path) if ffmpeg_path else None


def check_ffmpeg_installed() -> bool:
    """Check if FFmpeg is available."""
    return find_ffmpeg() is not None


def get_audio_output_path(input_path: Path) -> Path:
    """Generate output path for extracted audio."""
    return settings.temp_dir / f"{input_path.stem}_audio.wav"


def build_ffmpeg_command(input_path: Path, output_path: Path) -> list[str]:
    """Build FFmpeg command for audio extraction."""
    return [
        "ffmpeg",
        "-i", str(input_path),
        "-vn",                    # No video
        "-acodec", "pcm_s16le",   # PCM 16-bit
        "-ar", "16000",           # 16kHz sample rate (optimal for Whisper)
        "-ac", "1",               # Mono
        "-y",                     # Overwrite output
        str(output_path)
    ]


def extract_audio_sync(input_path: Path, output_path: Optional[Path] = None) -> Path:
    """
    Extract audio from video file synchronously.

    Args:
        input_path: Path to input video/audio file
        output_path: Optional custom output path

    Returns:
        Path to extracted audio file

    Raises:
        FFmpegNotFoundError: If FFmpeg is not installed
        AudioExtractionError: If extraction fails
        FileNotFoundError: If input file doesn't exist
    """
    if not check_ffmpeg_installed():
        raise FFmpegNotFoundError(
            "FFmpeg not found. Please install FFmpeg and ensure it's in your PATH."
        )

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    settings.ensure_directories()

    if output_path is None:
        output_path = get_audio_output_path(input_path)

    command = build_ffmpeg_command(input_path, output_path)

    try:
        subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise AudioExtractionError(
            f"FFmpeg failed: {e.stderr}"
        ) from e

    if not output_path.exists():
        raise AudioExtractionError("Audio extraction completed but output file not found")

    return output_path


async def extract_audio(input_path: Path, output_path: Optional[Path] = None) -> Path:
    """
    Extract audio from video file asynchronously.

    Args:
        input_path: Path to input video/audio file
        output_path: Optional custom output path

    Returns:
        Path to extracted audio file
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        extract_audio_sync,
        input_path,
        output_path
    )


def cleanup_audio_file(audio_path: Path) -> None:
    """Remove temporary audio file."""
    if audio_path.exists():
        audio_path.unlink()
