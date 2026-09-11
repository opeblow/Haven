"""Entry point for the Haven agents service."""

from __future__ import annotations

import uvicorn

from haven.config import get_settings


def main() -> None:
    """Run the Haven API server."""
    settings = get_settings()
    uvicorn.run(
        "haven.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
