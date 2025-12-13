"""Application configuration."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # App info
    app_name: str = "Video to Text Transcriber"
    app_version: str = "0.1.0"

    # Server settings
    host: str = "127.0.0.1"
    port: int = 8000

    # Paths
    temp_dir: Path = Path("temp")
    output_dir: Path = Path("output")

    # Whisper settings
    whisper_model: Literal["tiny", "base", "small", "medium", "large-v3"] = "base"
    whisper_device: Literal["auto", "cpu", "cuda"] = "auto"

    # File settings
    max_file_size_mb: int = 500
    allowed_extensions: set[str] = {
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
        ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"
    }

    # Output formats
    output_formats: set[str] = {".txt", ".srt", ".vtt"}

    class Config:
        env_prefix = "VTT_"

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
