"""FastAPI dependencies for shared services."""

from __future__ import annotations

from typing import cast

from fastapi import Header, HTTPException, Request, status

from core.service_container import ServiceContainer


def get_container(request: Request) -> ServiceContainer:
    """Return the shared service container from application state."""

    return cast(ServiceContainer, request.app.state.container)


def require_local_token(
    request: Request,
    x_auth_token: str | None = Header(default=None),
) -> None:
    """Protect endpoints when a local token is configured."""

    configured_token = request.app.state.container.settings.env.jarvis_auth_token
    if not configured_token:
        return
    if x_auth_token == configured_token:
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid local auth token.",
    )
