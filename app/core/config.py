"""Application configuration."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Default allowed file extensions
DEFAULT_ALLOWED_EXTENSIONS = frozenset({
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
    ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"
})

# Default output formats
DEFAULT_OUTPUT_FORMATS = frozenset({".txt", ".srt", ".vtt"})


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(env_prefix="VTT_")

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
    allowed_extensions: frozenset[str] = Field(default=DEFAULT_ALLOWED_EXTENSIONS)

    # Output formats
    output_formats: frozenset[str] = Field(default=DEFAULT_OUTPUT_FORMATS)

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
