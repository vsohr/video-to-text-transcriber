"""API routes for the transcription service."""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

from app.api.dependencies import get_jobs_store, get_transcription_svc
from app.core.config import settings
from app.core.models import (
    JobStatus,
    JobStatusResponse,
    OutputFormat,
    TranscriptionJob,
    TranscriptResponse,
    UploadResponse,
)
from app.services.audio import (
    AudioExtractionError,
    FFmpegNotFoundError,
    cleanup_audio_file,
    extract_audio_sync,
)
from app.services.transcription import TranscriptionError, TranscriptionService

router = APIRouter()


def _validate_file_extension(filename: str) -> None:
    """Validate that file has allowed extension."""
    ext = Path(filename).suffix.lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Allowed: {sorted(settings.allowed_extensions)}"
        )


def _validate_file_size(size: int) -> None:
    """Validate that file size is within limits."""
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if size > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )


async def _save_upload_file(upload_file: UploadFile, job_id: str) -> Path:
    """Save uploaded file to temp directory."""
    settings.ensure_directories()
    ext = Path(upload_file.filename or "file").suffix
    file_path = settings.temp_dir / f"{job_id}{ext}"

    content = await upload_file.read()
    _validate_file_size(len(content))

    file_path.write_bytes(content)
    return file_path


def _process_transcription(
    job: TranscriptionJob,
    jobs: Dict[str, TranscriptionJob],
    service: TranscriptionService
) -> None:
    """Background task to process transcription."""
    try:
        # Update status to extracting audio
        job.status = JobStatus.EXTRACTING_AUDIO
        job.progress = 0.0

        # Extract audio
        audio_path = extract_audio_sync(job.input_path)
        job.audio_path = audio_path
        job.progress = 10.0

        # Update status to transcribing
        job.status = JobStatus.TRANSCRIBING

        def update_progress(progress: float) -> None:
            # Scale progress from 10% to 100%
            job.progress = 10.0 + (progress * 0.9)

        # Transcribe
        result = service.transcribe_sync(audio_path, progress_callback=update_progress)

        # Update job with result
        job.result = result
        job.status = JobStatus.COMPLETED
        job.progress = 100.0
        job.completed_at = datetime.now(timezone.utc)

    except FFmpegNotFoundError as e:
        job.status = JobStatus.FAILED
        job.error_message = str(e)
    except AudioExtractionError as e:
        job.status = JobStatus.FAILED
        job.error_message = f"Audio extraction failed: {e}"
    except TranscriptionError as e:
        job.status = JobStatus.FAILED
        job.error_message = f"Transcription failed: {e}"
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_message = f"Unexpected error: {e}"
    finally:
        # Cleanup temp files
        if job.audio_path and job.audio_path.exists():
            cleanup_audio_file(job.audio_path)
        if job.input_path and job.input_path.exists():
            job.input_path.unlink()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    jobs: Dict[str, TranscriptionJob] = Depends(get_jobs_store),
    service: TranscriptionService = Depends(get_transcription_svc),
) -> UploadResponse:
    """
    Upload a video/audio file for transcription.

    Returns a job ID to track progress.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    _validate_file_extension(file.filename)

    # Generate job ID and save file
    job_id = str(uuid.uuid4())
    file_path = await _save_upload_file(file, job_id)

    # Create job
    job = TranscriptionJob(
        job_id=job_id,
        filename=file.filename,
        input_path=file_path,
    )
    jobs[job_id] = job

    # Start background processing
    background_tasks.add_task(_process_transcription, job, jobs, service)

    return UploadResponse(
        job_id=job_id,
        filename=file.filename,
        message="File uploaded successfully. Transcription started."
    )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    jobs: Dict[str, TranscriptionJob] = Depends(get_jobs_store),
) -> JobStatusResponse:
    """Get the status of a transcription job."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        filename=job.filename,
        error_message=job.error_message,
    )


@router.get("/transcript/{job_id}", response_model=TranscriptResponse)
async def get_transcript(
    job_id: str,
    jobs: Dict[str, TranscriptionJob] = Depends(get_jobs_store),
) -> TranscriptResponse:
    """Get the transcript for a completed job."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Current status: {job.status.value}"
        )

    if not job.result:
        raise HTTPException(status_code=500, detail="Job completed but no result found")

    return TranscriptResponse(
        job_id=job.job_id,
        filename=job.filename,
        text=job.result.text,
        segments=job.result.segments,
        language=job.result.language,
        duration=job.result.duration,
    )


@router.get("/download/{job_id}")
async def download_transcript(
    job_id: str,
    format: OutputFormat = OutputFormat.TXT,
    jobs: Dict[str, TranscriptionJob] = Depends(get_jobs_store),
) -> PlainTextResponse:
    """Download the transcript in specified format."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Current status: {job.status.value}"
        )

    if not job.result:
        raise HTTPException(status_code=500, detail="Job completed but no result found")

    content = _format_transcript(job.result, format)
    filename = Path(job.filename).stem + f".{format.value}"

    return PlainTextResponse(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


def _format_transcript(result, format: OutputFormat) -> str:
    """Format transcript in the specified output format."""
    if format == OutputFormat.TXT:
        return result.text

    elif format == OutputFormat.SRT:
        lines = []
        for i, segment in enumerate(result.segments, 1):
            start = _format_srt_time(segment.start)
            end = _format_srt_time(segment.end)
            lines.append(f"{i}")
            lines.append(f"{start} --> {end}")
            lines.append(segment.text)
            lines.append("")
        return "\n".join(lines)

    elif format == OutputFormat.VTT:
        lines = ["WEBVTT", ""]
        for segment in result.segments:
            start = _format_vtt_time(segment.start)
            end = _format_vtt_time(segment.end)
            lines.append(f"{start} --> {end}")
            lines.append(segment.text)
            lines.append("")
        return "\n".join(lines)

    return result.text


def _format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timestamp (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _format_vtt_time(seconds: float) -> str:
    """Format seconds as VTT timestamp (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
