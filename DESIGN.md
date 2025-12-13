# Design Document: Video to Text Transcriber

A local-first desktop application for transcribing video files to text. All processing happens on your machine - no data leaves your computer.

## Overview

Simple drag-and-drop interface to transcribe video/audio files into text documents.

```
┌─────────────────────────────────────┐
│ Video Transcriber              ─ □ x│
├─────────────────────────────────────┤
│                                     │
│     ┌───────────────────────┐       │
│     │                       │       │
│     │   Drop video here     │       │
│     │       or click        │       │
│     │                       │       │
│     └───────────────────────┘       │
│                                     │
│     [================    ] 70%      │
│                                     │
│     ┌─────────────────────────┐     │
│     │ Transcript appears here │     │
│     └─────────────────────────┘     │
│                                     │
│         [ Download .txt ]           │
│                                     │
└─────────────────────────────────────┘
```

## Architecture

```
┌────────────────────────────────────────┐
│            Desktop App (.exe)          │
├────────────────────────────────────────┤
│  PyWebView (native window wrapper)     │
│       │                                │
│       ▼                                │
│  FastAPI (embedded backend)            │
│       │                                │
│       ├──▶ FFmpeg (audio extraction)   │
│       │                                │
│       └──▶ Faster-Whisper (local AI)   │
│                                        │
│  HTML/CSS/JS (frontend UI)             │
└────────────────────────────────────────┘
```

### Data Flow

```
Video File (.mp4, .mkv, etc.)
         │
         ▼
    ┌─────────┐
    │ FFmpeg  │  Extract audio track
    └────┬────┘
         │
         ▼
    Audio (.wav)
         │
         ▼
┌─────────────────┐
│ Faster-Whisper  │  Transcribe speech to text
└────────┬────────┘
         │
         ▼
  Transcript (.txt, .srt, .vtt)
```

## Tech Stack

### Core Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Transcription Engine** | Faster-Whisper | Local AI speech-to-text |
| **Audio Extraction** | FFmpeg | Extract audio from video containers |
| **Backend API** | FastAPI (Python) | Handle uploads, orchestrate processing |
| **Frontend UI** | Vanilla HTML/CSS/JS | Drag-drop interface |
| **Desktop Wrapper** | PyWebView | Native window, no browser needed |
| **Packaging** | PyInstaller | Bundle into single executable |

### Why These Choices

**Faster-Whisper** over OpenAI Whisper:
- 4x faster transcription
- Lower memory usage
- Same accuracy (uses Whisper models)
- 100% local, no API calls

**FastAPI** over Flask/Django:
- Async support for file uploads
- Built-in OpenAPI docs
- Modern Python, type hints
- Lightweight

**PyWebView** over Electron/Tauri:
- Python-only stack (no JS build tools)
- Uses native OS webview (lightweight)
- Simple to integrate with FastAPI
- Easy packaging with PyInstaller

**Vanilla HTML/JS** over React/Vue:
- No build step required
- No node_modules
- Simple to modify
- Served directly by FastAPI

## Whisper Model Options

| Model | VRAM/RAM | Relative Speed | Use Case |
|-------|----------|----------------|----------|
| `tiny` | ~1 GB | Fastest | Quick drafts |
| `base` | ~1 GB | Fast | Good enough for most |
| `small` | ~2 GB | Medium | Better accuracy |
| `medium` | ~5 GB | Slower | High accuracy |
| `large-v3` | ~10 GB | Slowest | Best accuracy |

Default: `base` model (good balance of speed and accuracy)

## Output Formats

- **Plain text (.txt)** - Just the words
- **SRT (.srt)** - Subtitles with timestamps
- **VTT (.vtt)** - Web Video Text Tracks

## Project Structure

```
video-to-text-transcriber/
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point (PyWebView launch)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py        # API endpoint definitions
│   │   └── dependencies.py  # FastAPI dependencies
│   ├── services/
│   │   ├── __init__.py
│   │   ├── transcription.py # Transcription business logic
│   │   └── audio.py         # Audio extraction logic
│   └── core/
│       ├── __init__.py
│       ├── config.py        # App configuration
│       └── models.py        # Data models / schemas
├── static/
│   ├── index.html           # Main UI
│   ├── styles.css           # Styling
│   └── app.js               # Frontend logic
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── api/
│   │   └── test_routes.py
│   └── services/
│       ├── test_transcription.py
│       └── test_audio.py
├── requirements.txt         # Python dependencies
├── requirements-dev.txt     # Dev/test dependencies
├── pyinstaller.spec         # Packaging config
├── DESIGN.md                # This file
├── CLAUDE.md                # AI assistant instructions
└── README.md                # User documentation
```

### Layer Responsibilities

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **API** | `app/api/` | HTTP handling, validation, routing |
| **Services** | `app/services/` | Business logic, orchestration |
| **Core** | `app/core/` | Config, models, shared utilities |
| **Tests** | `tests/` | Unit and integration tests |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serve the UI |
| `POST` | `/upload` | Upload video file |
| `GET` | `/status/{job_id}` | Check transcription progress |
| `GET` | `/download/{job_id}` | Download transcript |

## Requirements

### System Requirements
- Windows 10+, macOS 10.14+, or Linux
- 4 GB RAM minimum (8 GB recommended)
- 2 GB disk space for models

### Dependencies
- Python 3.10+
- FFmpeg (bundled or system-installed)
- CUDA toolkit (optional, for GPU acceleration)

## Privacy

- All processing happens locally
- No internet connection required after initial setup
- No telemetry or analytics
- Video files never leave your machine
