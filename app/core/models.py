"""Data models and schemas."""

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


class JobStatus(str, Enum):
    """Transcription job status."""

    PENDING = "pending"
    EXTRACTING_AUDIO = "extracting_audio"
    TRANSCRIBING = "transcribing"
    COMPLETED = "completed"
    FAILED = "failed"


class OutputFormat(str, Enum):
    """Supported output formats."""

    TXT = "txt"
    SRT = "srt"
    VTT = "vtt"


class TranscriptionSegment(BaseModel):
    """A single segment of transcribed text with timing."""

    start: float = Field(description="Start time in seconds")
    end: float = Field(description="End time in seconds")
    text: str = Field(description="Transcribed text")


class TranscriptionResult(BaseModel):
    """Complete transcription result."""

    segments: list[TranscriptionSegment] = Field(default_factory=list)
    text: str = Field(default="", description="Full transcribed text")
    language: Optional[str] = Field(default=None, description="Detected language")
    duration: Optional[float] = Field(default=None, description="Audio duration in seconds")


class TranscriptionJob(BaseModel):
    """Represents a transcription job."""

    job_id: str = Field(description="Unique job identifier")
    filename: str = Field(description="Original filename")
    status: JobStatus = Field(default=JobStatus.PENDING)
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utc_now)
    completed_at: Optional[datetime] = Field(default=None)
    result: Optional[TranscriptionResult] = Field(default=None)

    # File paths (internal use)
    input_path: Optional[Path] = Field(default=None, exclude=True)
    audio_path: Optional[Path] = Field(default=None, exclude=True)


class UploadResponse(BaseModel):
    """Response after file upload."""

    job_id: str
    filename: str
    message: str


class JobStatusResponse(BaseModel):
    """Response for job status check."""

    job_id: str
    status: JobStatus
    progress: float
    filename: str
    error_message: Optional[str] = None


class TranscriptResponse(BaseModel):
    """Response containing transcript."""

    job_id: str
    filename: str
    text: str
    segments: list[TranscriptionSegment]
    language: Optional[str] = None
    duration: Optional[float] = None
