# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Project Overview

Local-first video-to-text transcription desktop app. See [DESIGN.md](DESIGN.md) for full architecture and tech stack details.

**Key principle: Everything runs locally. No data leaves the user's machine.**

## Tech Stack Summary

- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla HTML/CSS/JS
- **Transcription**: Faster-Whisper (local AI)
- **Audio extraction**: FFmpeg
- **Desktop wrapper**: PyWebView
- **Packaging**: PyInstaller

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run in development mode (browser)
uvicorn app.main:app --reload

# Run as desktop app
python -m app.main

# Build executable
pyinstaller pyinstaller.spec
```

## Project Structure

```
app/
├── main.py          # FastAPI + PyWebView entry point
├── transcriber.py   # Faster-Whisper wrapper
└── audio.py         # FFmpeg audio extraction

static/
├── index.html       # Main UI
├── styles.css       # Styling
└── app.js           # Frontend logic
```

## Software Engineering Principles

### Clean Code
- Write self-documenting code with clear naming
- Functions should do one thing and do it well
- Avoid magic numbers - use named constants
- Keep functions short (< 20 lines ideal)
- No dead code or commented-out blocks

### Small Files
- **Maximum 300 LOC per file** (hard limit: 500 LOC)
- If a file grows too large, split by responsibility
- Each file should have a single, clear purpose

### Separation of Concerns
- **API layer** (`app/api/`) - HTTP handling, request/response
- **Service layer** (`app/services/`) - Business logic
- **Core layer** (`app/core/`) - Domain models, utilities
- Frontend and backend are strictly separated
- No business logic in API endpoints

### Consistent Design Patterns
- Dependency injection for testability
- Repository pattern for data access if needed
- Use Python protocols/ABCs for interfaces
- Consistent error handling strategy

### Reusability
- Extract common functionality into utilities
- Design functions to be composable
- Avoid tight coupling between modules
- Use configuration over hardcoding

### Testability
- Write code that is easy to test in isolation
- Use dependency injection to mock dependencies
- Keep side effects at the edges of the system
- Pure functions where possible

### Unit Testing
- **Test everything** - aim for high coverage
- Tests live in `tests/` mirroring `app/` structure
- Use pytest as the test framework
- Test file naming: `test_<module>.py`
- Run tests: `pytest tests/`
- Each public function should have tests
- Test edge cases and error conditions

## Development Guidelines

### Backend (Python)
- Use async/await for I/O operations
- Handle large file uploads with streaming
- Report transcription progress via polling or SSE
- Clean up temporary files after processing
- Type hints on all function signatures

### Frontend (HTML/JS)
- Keep it simple - vanilla JS, no frameworks
- Support drag-and-drop file upload
- Show progress during transcription
- Allow downloading results in multiple formats
- Separate concerns: structure (HTML), style (CSS), behavior (JS)

### Transcription
- Default to `base` model for balance of speed/accuracy
- Support model selection in UI for power users
- Handle long videos by processing in chunks if needed

## Progress Tracking

**Always update [PROGRESS.md](PROGRESS.md) when working on this project.**

- Check off tasks as you complete them
- Move completed tasks to the "Completed Tasks" section
- Add any blockers or notes to the "Notes" section
- Before starting work, review PROGRESS.md to see current status
- After completing work, update PROGRESS.md to reflect changes

This ensures continuity across sessions and prevents missed tasks.

## Documentation Maintenance

**Keep [DESIGN.md](DESIGN.md) up to date with major decisions.**

Update DESIGN.md when:
- Architecture changes (new layers, components, or data flow)
- Tech stack changes (swapping libraries, adding dependencies)
- API changes (new endpoints, modified contracts)
- New design patterns or conventions are adopted
- Project structure changes significantly

This keeps the design document as the single source of truth.

## Key Files to Reference

- [DESIGN.md](DESIGN.md) - Full architecture, data flow, API endpoints
- [PROGRESS.md](PROGRESS.md) - Current implementation status and task tracking
