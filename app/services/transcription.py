"""Transcription service using Faster-Whisper."""

import asyncio
from pathlib import Path
from typing import Callable, Optional

from app.core.config import settings
from app.core.models import TranscriptionResult, TranscriptionSegment


class TranscriptionError(Exception):
    """Raised when transcription fails."""

    pass


# Type alias for progress callback
ProgressCallback = Callable[[float], None]


class TranscriptionService:
    """Service for transcribing audio using Faster-Whisper."""

    def __init__(self) -> None:
        self._model = None
        self._model_name: Optional[str] = None

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None

    @property
    def model_name(self) -> Optional[str]:
        """Get currently loaded model name."""
        return self._model_name

    def load_model(self, model_name: Optional[str] = None) -> None:
        """
        Load Whisper model.

        Args:
            model_name: Model to load (tiny, base, small, medium, large-v3)
        """
        from faster_whisper import WhisperModel

        model_name = model_name or settings.whisper_model
        device = settings.whisper_device

        if device == "auto":
            device = "cuda" if self._cuda_available() else "cpu"

        compute_type = "float16" if device == "cuda" else "int8"

        self._model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type
        )
        self._model_name = model_name

    def _cuda_available(self) -> bool:
        """Check if CUDA is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def unload_model(self) -> None:
        """Unload model to free memory."""
        self._model = None
        self._model_name = None

    def transcribe_sync(
        self,
        audio_path: Path,
        progress_callback: Optional[ProgressCallback] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio file synchronously.

        Args:
            audio_path: Path to audio file
            progress_callback: Optional callback for progress updates

        Returns:
            TranscriptionResult with segments and full text
        """
        if not self.is_loaded:
            self.load_model()

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            segments_generator, info = self._model.transcribe(
                str(audio_path),
                beam_size=5,
                word_timestamps=False
            )

            segments: list[TranscriptionSegment] = []
            full_text_parts: list[str] = []

            duration = info.duration if info.duration else 1.0

            for segment in segments_generator:
                segments.append(TranscriptionSegment(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text.strip()
                ))
                full_text_parts.append(segment.text.strip())

                if progress_callback:
                    progress = min((segment.end / duration) * 100, 100.0)
                    progress_callback(progress)

            return TranscriptionResult(
                segments=segments,
                text=" ".join(full_text_parts),
                language=info.language,
                duration=info.duration
            )

        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}") from e

    async def transcribe(
        self,
        audio_path: Path,
        progress_callback: Optional[ProgressCallback] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio file asynchronously.

        Args:
            audio_path: Path to audio file
            progress_callback: Optional callback for progress updates

        Returns:
            TranscriptionResult with segments and full text
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.transcribe_sync,
            audio_path,
            progress_callback
        )


# Global service instance (lazy loaded)
_transcription_service: Optional[TranscriptionService] = None


def get_transcription_service() -> TranscriptionService:
    """Get or create the global transcription service."""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service
