# Video to Text Transcriber

A local-first desktop application for transcribing video and audio files to text. All processing happens on your machine - your files never leave your computer.

## Features

- Drag-and-drop file upload
- Supports many formats: MP4, MKV, AVI, MOV, MP3, WAV, M4A, and more
- Real-time progress tracking
- Export as plain text (.txt), subtitles (.srt), or WebVTT (.vtt)
- 100% local processing - no internet required after setup
- Powered by OpenAI's Whisper (via faster-whisper)

## Requirements

- Python 3.10+
- FFmpeg (must be installed and in PATH)
- 4 GB RAM minimum (8 GB recommended)
- 2 GB disk space for Whisper models

## Installation

### 1. Install FFmpeg

**Windows:**
```bash
# Using winget
winget install FFmpeg

# Or download from https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
sudo dnf install ffmpeg  # Fedora
```

### 2. Install Python dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

## Usage

### Desktop App (recommended)

```bash
python -m app.main
```

This opens the app in a native desktop window.

### Server Mode (development)

```bash
python -m app.main --server
```

Then open http://localhost:8000 in your browser.

### Using the App

1. Drop a video or audio file onto the upload area
2. Wait for transcription (progress shown in real-time)
3. Download the result as TXT, SRT, or VTT

## Building Executable

To create a standalone executable:

```bash
# Install PyInstaller
pip install pyinstaller

# Build the executable
pyinstaller pyinstaller.spec

# The executable will be in dist/VideoTranscriber/
```

### Distribution

After building:
- **Windows**: Distribute the `dist/VideoTranscriber/` folder (or create an installer)
- **macOS**: Create a .app bundle or distribute the folder
- **Linux**: Distribute the folder or create a .deb/.rpm package

Note: Users will still need FFmpeg installed separately.

## Configuration

Environment variables (prefix: `VTT_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `VTT_HOST` | `127.0.0.1` | Server host |
| `VTT_PORT` | `8000` | Server port |
| `VTT_WHISPER_MODEL` | `base` | Whisper model (tiny/base/small/medium/large-v3) |
| `VTT_WHISPER_DEVICE` | `auto` | Device (auto/cpu/cuda) |
| `VTT_MAX_FILE_SIZE_MB` | `500` | Maximum file size in MB |

## Whisper Models

| Model | RAM | Speed | Accuracy |
|-------|-----|-------|----------|
| tiny | ~1 GB | Fastest | Basic |
| base | ~1 GB | Fast | Good |
| small | ~2 GB | Medium | Better |
| medium | ~5 GB | Slower | Great |
| large-v3 | ~10 GB | Slowest | Best |

The model is downloaded automatically on first use.

## Project Structure

```
video-to-text-transcriber/
├── app/
│   ├── api/           # FastAPI routes and dependencies
│   ├── core/          # Configuration and models
│   ├── services/      # Audio extraction and transcription
│   └── main.py        # Entry point
├── static/            # Frontend (HTML/CSS/JS)
├── tests/             # Unit tests
├── requirements.txt   # Production dependencies
└── pyinstaller.spec   # Packaging configuration
```

## Development

```bash
# Run tests
pytest tests/

# Run with hot reload
uvicorn app.main:app --reload

# Type checking
mypy app/

# Linting
ruff check app/
```

## License

MIT

## Privacy

- All transcription happens locally on your machine
- No data is sent to any external servers
- No telemetry or analytics
- Your files remain private
