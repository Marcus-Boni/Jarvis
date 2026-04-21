"""Voice API placeholders for upcoming streaming audio work."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import require_local_token

router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/stream", dependencies=[Depends(require_local_token)])
async def voice_stream_status() -> dict[str, str]:
    """Phase 0 placeholder for voice streaming."""

    return {
        "status": "not_ready",
        "message": "The live voice pipeline will be enabled in Phase 1.",
    }

