"""FastAPI dependencies for dependency injection."""

from typing import Dict

from app.core.models import TranscriptionJob
from app.services.transcription import TranscriptionService, get_transcription_service


# In-memory job storage (for simplicity - could be replaced with database)
_jobs: Dict[str, TranscriptionJob] = {}


def get_jobs_store() -> Dict[str, TranscriptionJob]:
    """Get the jobs storage dictionary."""
    return _jobs


def get_transcription_svc() -> TranscriptionService:
    """Get the transcription service instance."""
    return get_transcription_service()


def clear_jobs_store() -> None:
    """Clear all jobs from storage. Useful for testing."""
    _jobs.clear()
