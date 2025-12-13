"""Tests for API routes."""

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import clear_jobs_store, get_jobs_store
from app.api.routes import _format_srt_time, _format_vtt_time
from app.core.models import (
    JobStatus,
    TranscriptionJob,
    TranscriptionResult,
    TranscriptionSegment,
)
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    clear_jobs_store()
    return TestClient(app)


@pytest.fixture
def sample_job() -> TranscriptionJob:
    """Create a sample transcription job."""
    return TranscriptionJob(
        job_id="test-job-123",
        filename="test_video.mp4",
    )


@pytest.fixture
def completed_job() -> TranscriptionJob:
    """Create a completed transcription job."""
    job = TranscriptionJob(
        job_id="completed-job-456",
        filename="test_video.mp4",
        status=JobStatus.COMPLETED,
        progress=100.0,
    )
    job.result = TranscriptionResult(
        text="Hello world",
        segments=[
            TranscriptionSegment(start=0.0, end=1.0, text="Hello"),
            TranscriptionSegment(start=1.0, end=2.0, text="world"),
        ],
        language="en",
        duration=2.0,
    )
    return job


class TestUploadEndpoint:
    """Tests for POST /api/upload endpoint."""

    def test_upload_requires_file(self, client: TestClient) -> None:
        """Should return 422 when no file provided."""
        response = client.post("/api/upload")
        assert response.status_code == 422

    def test_upload_rejects_invalid_extension(self, client: TestClient) -> None:
        """Should reject files with invalid extensions."""
        file_content = b"fake content"
        files = {"file": ("test.xyz", io.BytesIO(file_content), "application/octet-stream")}

        response = client.post("/api/upload", files=files)
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"]

    def test_upload_accepts_valid_file(self, client: TestClient) -> None:
        """Should accept valid video file."""
        file_content = b"fake video content"
        files = {"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}

        with patch("app.api.routes._process_transcription"):
            with patch("app.api.routes.settings") as mock_settings:
                mock_settings.allowed_extensions = frozenset({".mp4"})
                mock_settings.max_file_size_mb = 500
                mock_settings.temp_dir = Path("/tmp")
                mock_settings.ensure_directories = MagicMock()

                response = client.post("/api/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["filename"] == "test.mp4"
        assert "message" in data


class TestStatusEndpoint:
    """Tests for GET /api/status/{job_id} endpoint."""

    def test_status_returns_404_for_unknown_job(self, client: TestClient) -> None:
        """Should return 404 for unknown job ID."""
        response = client.get("/api/status/unknown-job-id")
        assert response.status_code == 404

    def test_status_returns_job_info(
        self, client: TestClient, sample_job: TranscriptionJob
    ) -> None:
        """Should return job status information."""
        jobs = get_jobs_store()
        jobs[sample_job.job_id] = sample_job

        response = client.get(f"/api/status/{sample_job.job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == sample_job.job_id
        assert data["status"] == "pending"
        assert data["progress"] == 0.0
        assert data["filename"] == sample_job.filename


class TestTranscriptEndpoint:
    """Tests for GET /api/transcript/{job_id} endpoint."""

    def test_transcript_returns_404_for_unknown_job(self, client: TestClient) -> None:
        """Should return 404 for unknown job ID."""
        response = client.get("/api/transcript/unknown-job-id")
        assert response.status_code == 404

    def test_transcript_returns_400_for_incomplete_job(
        self, client: TestClient, sample_job: TranscriptionJob
    ) -> None:
        """Should return 400 for incomplete job."""
        jobs = get_jobs_store()
        jobs[sample_job.job_id] = sample_job

        response = client.get(f"/api/transcript/{sample_job.job_id}")

        assert response.status_code == 400
        assert "not completed" in response.json()["detail"]

    def test_transcript_returns_result(
        self, client: TestClient, completed_job: TranscriptionJob
    ) -> None:
        """Should return transcript for completed job."""
        jobs = get_jobs_store()
        jobs[completed_job.job_id] = completed_job

        response = client.get(f"/api/transcript/{completed_job.job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Hello world"
        assert len(data["segments"]) == 2
        assert data["language"] == "en"
        assert data["duration"] == 2.0


class TestDownloadEndpoint:
    """Tests for GET /api/download/{job_id} endpoint."""

    def test_download_returns_404_for_unknown_job(self, client: TestClient) -> None:
        """Should return 404 for unknown job ID."""
        response = client.get("/api/download/unknown-job-id")
        assert response.status_code == 404

    def test_download_returns_txt_format(
        self, client: TestClient, completed_job: TranscriptionJob
    ) -> None:
        """Should return plain text transcript."""
        jobs = get_jobs_store()
        jobs[completed_job.job_id] = completed_job

        response = client.get(f"/api/download/{completed_job.job_id}?format=txt")

        assert response.status_code == 200
        assert response.text == "Hello world"
        assert "attachment" in response.headers.get("content-disposition", "")

    def test_download_returns_srt_format(
        self, client: TestClient, completed_job: TranscriptionJob
    ) -> None:
        """Should return SRT format transcript."""
        jobs = get_jobs_store()
        jobs[completed_job.job_id] = completed_job

        response = client.get(f"/api/download/{completed_job.job_id}?format=srt")

        assert response.status_code == 200
        assert "00:00:00,000 --> 00:00:01,000" in response.text
        assert "Hello" in response.text

    def test_download_returns_vtt_format(
        self, client: TestClient, completed_job: TranscriptionJob
    ) -> None:
        """Should return VTT format transcript."""
        jobs = get_jobs_store()
        jobs[completed_job.job_id] = completed_job

        response = client.get(f"/api/download/{completed_job.job_id}?format=vtt")

        assert response.status_code == 200
        assert "WEBVTT" in response.text
        assert "00:00:00.000 --> 00:00:01.000" in response.text


class TestTimeFormatting:
    """Tests for time formatting functions."""

    def test_format_srt_time(self) -> None:
        """Should format time correctly for SRT."""
        assert _format_srt_time(0.0) == "00:00:00,000"
        assert _format_srt_time(1.5) == "00:00:01,500"
        assert _format_srt_time(61.123) == "00:01:01,123"
        assert _format_srt_time(3661.999) == "01:01:01,999"

    def test_format_vtt_time(self) -> None:
        """Should format time correctly for VTT."""
        assert _format_vtt_time(0.0) == "00:00:00.000"
        assert _format_vtt_time(1.5) == "00:00:01.500"
        assert _format_vtt_time(61.123) == "00:01:01.123"
        assert _format_vtt_time(3661.999) == "01:01:01.999"
