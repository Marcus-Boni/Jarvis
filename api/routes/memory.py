"""Memory inspection endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.dependencies import get_container, require_local_token
from core.models import ContextDocument
from core.service_container import ServiceContainer

router = APIRouter(prefix="/api/memory", tags=["memory"])


class MemoryQueryRequest(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=20)


@router.post("/query", dependencies=[Depends(require_local_token)])
async def query_memory(
    payload: MemoryQueryRequest,
    container: ServiceContainer = Depends(get_container),
) -> dict[str, list[dict[str, object]]]:
    """Query the current memory store."""

    items = await container.memory_store.query(query_text=payload.query, limit=payload.limit)
    return {"items": [item.model_dump() for item in items]}

