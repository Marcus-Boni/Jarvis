"""Skill management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.dependencies import get_container, require_local_token
from core.service_container import ServiceContainer

router = APIRouter(prefix="/api/skills", tags=["skills"])


class SkillToggleRequest(BaseModel):
    enabled: bool


@router.get("", dependencies=[Depends(require_local_token)])
async def list_skills(container: ServiceContainer = Depends(get_container)) -> dict[str, list[dict[str, object]]]:
    """List loaded skills and status."""

    return {"items": [skill.status_payload() for skill in container.skill_loader.list_all()]}


@router.post("/{skill_name}", dependencies=[Depends(require_local_token)])
async def toggle_skill(
    skill_name: str,
    payload: SkillToggleRequest,
    container: ServiceContainer = Depends(get_container),
) -> dict[str, object]:
    """Enable or disable a skill."""

    did_update = container.skill_loader.set_enabled(skill_name=skill_name, enabled=payload.enabled)
    if did_update:
        return {"skill_name": skill_name, "enabled": payload.enabled}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")

