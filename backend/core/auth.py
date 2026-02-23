"""Simple password-based authentication."""

from fastapi import Depends, HTTPException, Request

from core.config import Settings, get_settings


def verify_password(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    """Check X-App-Password header if APP_PASSWORD is configured."""
    if not settings.app_password:
        return  # No password set — open access
    token = request.headers.get("X-App-Password", "")
    if token != settings.app_password:
        raise HTTPException(status_code=401, detail="Invalid password")
