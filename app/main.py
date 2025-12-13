"""Main application entry point."""

import sys
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings


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
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

    return app


# Create the app instance
app = create_app()


def run_server() -> None:
    """Run the FastAPI server with uvicorn."""
    import uvicorn

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info",
    )


def run_desktop() -> None:
    """Run the application as a desktop app with PyWebView."""
    import webview

    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Create desktop window
    webview.create_window(
        title=settings.app_name,
        url=f"http://{settings.host}:{settings.port}",
        width=900,
        height=700,
        resizable=True,
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
