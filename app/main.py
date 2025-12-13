"""Main application entry point."""

import sys
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings


def get_static_dir() -> Path:
    """Get the static files directory, handling both dev and packaged modes."""
    # Check if running as packaged app (PyInstaller)
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = Path(sys._MEIPASS)
    else:
        # Running in development
        base_path = Path(__file__).parent.parent

    return base_path / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    settings.ensure_directories()
    yield
    # Shutdown (cleanup if needed)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    # Include API routes
    app.include_router(router, prefix="/api")

    # Mount static files for frontend
    static_dir = get_static_dir()
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app


# Create the app instance
app = create_app()


def run_server(ready_event: threading.Event = None) -> None:
    """Run the FastAPI server with uvicorn."""
    import uvicorn

    class Server(uvicorn.Server):
        """Custom server to signal when ready."""

        def install_signal_handlers(self):
            # Skip signal handlers in thread
            pass

    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_level="warning",
    )
    server = Server(config)

    if ready_event:
        # Signal ready after server starts
        original_startup = server.startup

        async def startup_with_signal(*args, **kwargs):
            await original_startup(*args, **kwargs)
            ready_event.set()

        server.startup = startup_with_signal

    server.run()


def run_desktop() -> None:
    """Run the application as a desktop app with PyWebView."""
    import webview

    # Event to signal when server is ready
    server_ready = threading.Event()

    # Start server in background thread
    server_thread = threading.Thread(
        target=run_server,
        args=(server_ready,),
        daemon=True
    )
    server_thread.start()

    # Wait for server to be ready (max 10 seconds)
    server_ready.wait(timeout=10)

    # Small additional delay to ensure server is fully ready
    time.sleep(0.5)

    # Create desktop window
    webview.create_window(
        title=settings.app_name,
        url=f"http://{settings.host}:{settings.port}",
        width=900,
        height=700,
        resizable=True,
        min_size=(600, 500),
    )
    webview.start()


def main() -> None:
    """Main entry point."""
    if "--server" in sys.argv:
        # Run as server only (for development)
        run_server()
    else:
        # Run as desktop app (default)
        run_desktop()


if __name__ == "__main__":
    main()
