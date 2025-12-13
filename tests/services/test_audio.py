"""Tests for audio extraction service."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.audio import (
    AudioExtractionError,
    FFmpegNotFoundError,
    build_ffmpeg_command,
    check_ffmpeg_installed,
    cleanup_audio_file,
    extract_audio_sync,
    find_ffmpeg,
    get_audio_output_path,
)


class TestFindFFmpeg:
    """Tests for find_ffmpeg function."""

    def test_returns_path_when_found(self) -> None:
        """Should return Path when FFmpeg is found."""
        with patch("app.services.audio.shutil.which", return_value="/usr/bin/ffmpeg"):
            result = find_ffmpeg()
            assert result == Path("/usr/bin/ffmpeg")

    def test_returns_none_when_not_found(self) -> None:
        """Should return None when FFmpeg is not found."""
        with patch("app.services.audio.shutil.which", return_value=None):
            result = find_ffmpeg()
            assert result is None


class TestCheckFFmpegInstalled:
    """Tests for check_ffmpeg_installed function."""

    def test_returns_true_when_installed(self) -> None:
        """Should return True when FFmpeg is installed."""
        with patch("app.services.audio.shutil.which", return_value="/usr/bin/ffmpeg"):
            assert check_ffmpeg_installed() is True

    def test_returns_false_when_not_installed(self) -> None:
        """Should return False when FFmpeg is not installed."""
        with patch("app.services.audio.shutil.which", return_value=None):
            assert check_ffmpeg_installed() is False


class TestGetAudioOutputPath:
    """Tests for get_audio_output_path function."""

    def test_generates_correct_output_path(self, temp_dir: Path) -> None:
        """Should generate correct output path with _audio.wav suffix."""
        input_path = temp_dir / "my_video.mp4"
        with patch("app.services.audio.settings") as mock_settings:
            mock_settings.temp_dir = temp_dir
            result = get_audio_output_path(input_path)
            assert result == temp_dir / "my_video_audio.wav"


class TestBuildFFmpegCommand:
    """Tests for build_ffmpeg_command function."""

    def test_builds_correct_command(self, temp_dir: Path) -> None:
        """Should build correct FFmpeg command."""
        input_path = temp_dir / "input.mp4"
        output_path = temp_dir / "output.wav"

        command = build_ffmpeg_command(input_path, output_path)

        assert command[0] == "ffmpeg"
        assert "-i" in command
        assert str(input_path) in command
        assert str(output_path) in command
        assert "-vn" in command  # No video
        assert "-ar" in command  # Sample rate
        assert "16000" in command  # 16kHz
        assert "-ac" in command  # Channels
        assert "1" in command  # Mono


class TestExtractAudioSync:
    """Tests for extract_audio_sync function."""

    def test_raises_error_when_ffmpeg_not_found(self, temp_dir: Path) -> None:
        """Should raise FFmpegNotFoundError when FFmpeg not installed."""
        input_path = temp_dir / "video.mp4"
        input_path.touch()

        with patch("app.services.audio.check_ffmpeg_installed", return_value=False):
            with pytest.raises(FFmpegNotFoundError):
                extract_audio_sync(input_path)

    def test_raises_error_when_input_not_found(self, temp_dir: Path) -> None:
        """Should raise FileNotFoundError when input doesn't exist."""
        input_path = temp_dir / "nonexistent.mp4"

        with patch("app.services.audio.check_ffmpeg_installed", return_value=True):
            with pytest.raises(FileNotFoundError):
                extract_audio_sync(input_path)

    def test_successful_extraction(self, temp_dir: Path) -> None:
        """Should extract audio successfully."""
        input_path = temp_dir / "video.mp4"
        input_path.touch()
        output_path = temp_dir / "audio.wav"

        with patch("app.services.audio.check_ffmpeg_installed", return_value=True):
            with patch("app.services.audio.settings") as mock_settings:
                mock_settings.temp_dir = temp_dir
                mock_settings.ensure_directories = MagicMock()

                with patch("app.services.audio.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    # Create output file to simulate successful extraction
                    output_path.touch()

                    result = extract_audio_sync(input_path, output_path)
                    assert result == output_path


class TestCleanupAudioFile:
    """Tests for cleanup_audio_file function."""

    def test_removes_existing_file(self, temp_dir: Path) -> None:
        """Should remove file when it exists."""
        audio_path = temp_dir / "audio.wav"
        audio_path.touch()

        cleanup_audio_file(audio_path)
        assert not audio_path.exists()

    def test_handles_nonexistent_file(self, temp_dir: Path) -> None:
        """Should not raise error for nonexistent file."""
        audio_path = temp_dir / "nonexistent.wav"
        cleanup_audio_file(audio_path)  # Should not raise
