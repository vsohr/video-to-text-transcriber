"""Tests for transcription service."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.models import TranscriptionResult, TranscriptionSegment
from app.services.transcription import (
    TranscriptionError,
    TranscriptionService,
    get_transcription_service,
)


class TestTranscriptionService:
    """Tests for TranscriptionService class."""

    def test_initial_state(self) -> None:
        """Should start with no model loaded."""
        service = TranscriptionService()
        assert service.is_loaded is False
        assert service.model_name is None

    def test_is_loaded_property(self) -> None:
        """Should correctly report loaded state."""
        service = TranscriptionService()
        service._model = MagicMock()
        assert service.is_loaded is True

    def test_unload_model(self) -> None:
        """Should unload model and reset state."""
        service = TranscriptionService()
        service._model = MagicMock()
        service._model_name = "base"

        service.unload_model()

        assert service._model is None
        assert service._model_name is None
        assert service.is_loaded is False

    def test_load_model_uses_settings_default(self) -> None:
        """Should use settings default when no model specified."""
        service = TranscriptionService()

        with patch("app.services.transcription.settings") as mock_settings:
            mock_settings.whisper_model = "small"
            mock_settings.whisper_device = "cpu"

            with patch("faster_whisper.WhisperModel") as mock_whisper:
                service.load_model()

                mock_whisper.assert_called_once_with(
                    "small",
                    device="cpu",
                    compute_type="int8"
                )
                assert service.model_name == "small"

    def test_load_model_with_custom_name(self) -> None:
        """Should use specified model name."""
        service = TranscriptionService()

        with patch("app.services.transcription.settings") as mock_settings:
            mock_settings.whisper_device = "cpu"

            with patch("faster_whisper.WhisperModel") as mock_whisper:
                service.load_model("tiny")

                mock_whisper.assert_called_once_with(
                    "tiny",
                    device="cpu",
                    compute_type="int8"
                )
                assert service.model_name == "tiny"

    def test_cuda_available_with_torch(self) -> None:
        """Should check CUDA availability via torch."""
        service = TranscriptionService()

        with patch.dict("sys.modules", {"torch": MagicMock()}):
            import sys
            sys.modules["torch"].cuda.is_available.return_value = True
            assert service._cuda_available() is True

    def test_cuda_not_available_without_torch(self) -> None:
        """Should return False when torch not installed."""
        service = TranscriptionService()

        with patch.dict("sys.modules", {"torch": None}):
            with patch("builtins.__import__", side_effect=ImportError):
                assert service._cuda_available() is False

    def test_transcribe_sync_file_not_found(self, temp_dir: Path) -> None:
        """Should raise error when audio file not found."""
        service = TranscriptionService()
        service._model = MagicMock()

        with pytest.raises(FileNotFoundError):
            service.transcribe_sync(temp_dir / "nonexistent.wav")

    def test_transcribe_sync_loads_model_if_needed(self, temp_dir: Path) -> None:
        """Should auto-load model if not loaded."""
        service = TranscriptionService()
        audio_path = temp_dir / "audio.wav"
        audio_path.touch()

        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 1.0
        mock_segment.text = "Hello world"

        mock_info = MagicMock()
        mock_info.duration = 1.0
        mock_info.language = "en"

        # Track if load_model was called
        load_model_called = False

        def mock_load_model(model_name=None):
            nonlocal load_model_called
            load_model_called = True
            service._model = MagicMock()
            service._model.transcribe.return_value = ([mock_segment], mock_info)

        with patch.object(service, "load_model", side_effect=mock_load_model):
            result = service.transcribe_sync(audio_path)
            assert load_model_called
            assert isinstance(result, TranscriptionResult)

    def test_transcribe_sync_with_progress_callback(self, temp_dir: Path) -> None:
        """Should call progress callback during transcription."""
        service = TranscriptionService()
        audio_path = temp_dir / "audio.wav"
        audio_path.touch()

        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 5.0
        mock_segment.text = "Test segment"

        mock_info = MagicMock()
        mock_info.duration = 10.0
        mock_info.language = "en"

        service._model = MagicMock()
        service._model.transcribe.return_value = ([mock_segment], mock_info)

        progress_values: list[float] = []
        callback = lambda p: progress_values.append(p)

        service.transcribe_sync(audio_path, progress_callback=callback)

        assert len(progress_values) > 0
        assert progress_values[0] == 50.0  # 5/10 * 100

    def test_transcribe_sync_returns_correct_result(self, temp_dir: Path) -> None:
        """Should return correct TranscriptionResult."""
        service = TranscriptionService()
        audio_path = temp_dir / "audio.wav"
        audio_path.touch()

        mock_segment1 = MagicMock()
        mock_segment1.start = 0.0
        mock_segment1.end = 2.0
        mock_segment1.text = "Hello"

        mock_segment2 = MagicMock()
        mock_segment2.start = 2.0
        mock_segment2.end = 4.0
        mock_segment2.text = "world"

        mock_info = MagicMock()
        mock_info.duration = 4.0
        mock_info.language = "en"

        service._model = MagicMock()
        service._model.transcribe.return_value = (
            [mock_segment1, mock_segment2],
            mock_info
        )

        result = service.transcribe_sync(audio_path)

        assert result.text == "Hello world"
        assert len(result.segments) == 2
        assert result.segments[0].text == "Hello"
        assert result.segments[1].text == "world"
        assert result.language == "en"
        assert result.duration == 4.0


class TestGetTranscriptionService:
    """Tests for get_transcription_service function."""

    def test_returns_singleton(self) -> None:
        """Should return same instance on multiple calls."""
        with patch("app.services.transcription._transcription_service", None):
            service1 = get_transcription_service()
            service2 = get_transcription_service()
            assert service1 is service2

    def test_creates_new_instance_if_none(self) -> None:
        """Should create new instance if none exists."""
        with patch("app.services.transcription._transcription_service", None):
            service = get_transcription_service()
            assert isinstance(service, TranscriptionService)
