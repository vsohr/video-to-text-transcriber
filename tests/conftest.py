"""Pytest fixtures and configuration."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_audio_path(temp_dir: Path) -> Path:
    """Create a dummy audio file path for testing."""
    audio_path = temp_dir / "test_audio.wav"
    # Create empty file for path testing
    audio_path.touch()
    return audio_path


@pytest.fixture
def sample_video_path(temp_dir: Path) -> Path:
    """Create a dummy video file path for testing."""
    video_path = temp_dir / "test_video.mp4"
    video_path.touch()
    return video_path
