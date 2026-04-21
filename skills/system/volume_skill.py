"""Windows system volume and media key control skill."""

from __future__ import annotations

import asyncio
import ctypes
import importlib
import os
import re
from typing import Any, ClassVar

from core.models import Intent, IntentCategory, RequestContext, SkillResult
from skills.base_skill import BaseSkill


class VolumeSkill(BaseSkill):
    """Controls Windows system volume and media playback keys."""

    name: ClassVar[str] = "volume"
    description: ClassVar[str] = "Controla volume do sistema e teclas de midia no Windows."
    triggers: ClassVar[list[str]] = [
        "volume",
        "aumentar volume",
        "diminuir volume",
        "mudo",
        "silenciar",
        "mute",
        "unmute",
        "proxima musica",
        "musica anterior",
        "play pause",
    ]

    async def can_handle(self, intent: Intent) -> float:
        lowered_text = intent.raw_text.lower()
        volume_words = ["volume", "som", "mudo", "silenci", "mute", "audio", "aumentar", "baixar"]
        media_words = ["proxima", "anterior", "play", "pause", "pausa", "avancar"]
        if intent.category is IntentCategory.VOLUME:
            return 0.9
        if any(word in lowered_text for word in volume_words + media_words):
            return 0.88
        return 0.0

    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        del context
        if os.name != "nt":
            return SkillResult(
                skill_name=self.name,
                success=False,
                message="Controle de volume/midia disponivel apenas no Windows.",
            )
        lowered_text = intent.raw_text.lower()
        try:
            if "mudo" in lowered_text or "silenci" in lowered_text or "mute" in lowered_text:
                result = await asyncio.to_thread(self._toggle_mute)
                return SkillResult(skill_name=self.name, success=True, message=result)

            if "aumentar" in lowered_text or "subir" in lowered_text or "mais" in lowered_text:
                amount = self._extract_amount(lowered_text, default=10)
                result = await asyncio.to_thread(self._change_volume, amount)
                return SkillResult(skill_name=self.name, success=True, message=result)

            if "diminuir" in lowered_text or "baixar" in lowered_text or "menos" in lowered_text:
                amount = self._extract_amount(lowered_text, default=10)
                result = await asyncio.to_thread(self._change_volume, -amount)
                return SkillResult(skill_name=self.name, success=True, message=result)

            if any(word in lowered_text for word in ["proxima", "next", "avancar"]):
                self._send_media_key("next")
                return SkillResult(
                    skill_name=self.name,
                    success=True,
                    message="Proxima faixa.",
                )

            if any(word in lowered_text for word in ["anterior", "voltar", "previous"]):
                self._send_media_key("previous")
                return SkillResult(
                    skill_name=self.name,
                    success=True,
                    message="Faixa anterior.",
                )

            if any(word in lowered_text for word in ["play", "pause", "pausa"]):
                self._send_media_key("play_pause")
                return SkillResult(skill_name=self.name, success=True, message="Play/Pause.")

            return SkillResult(
                skill_name=self.name,
                success=False,
                message="Nao entendi o comando de volume ou midia.",
            )
        except Exception as exc:  # pragma: no cover
            return SkillResult(
                skill_name=self.name,
                success=False,
                message=f"Erro ao controlar audio: {exc}",
            )

    def _get_volume_interface(self) -> Any:
        comtypes_module = importlib.import_module("comtypes")
        pycaw_module = importlib.import_module("pycaw.pycaw")

        clsctx_all = comtypes_module.CLSCTX_ALL
        audio_utilities = pycaw_module.AudioUtilities
        endpoint_volume = pycaw_module.IAudioEndpointVolume
        devices = audio_utilities.GetSpeakers()
        interface = devices.Activate(endpoint_volume._iid_, clsctx_all, None)
        return ctypes.cast(interface, ctypes.POINTER(endpoint_volume))

    def _change_volume(self, delta_percent: int) -> str:
        volume_interface = self._get_volume_interface()
        current_level = float(volume_interface.GetMasterVolumeLevelScalar()) * 100
        new_level = max(0.0, min(100.0, current_level + delta_percent))
        volume_interface.SetMasterVolumeLevelScalar(new_level / 100, None)
        return f"Volume: {int(new_level)}%"

    def _toggle_mute(self) -> str:
        volume_interface = self._get_volume_interface()
        is_muted = bool(volume_interface.GetMute())
        volume_interface.SetMute(not is_muted, None)
        return "Audio ativado." if is_muted else "Audio silenciado."

    def _send_media_key(self, key: str) -> None:
        vk_map = {
            "play_pause": 0xB3,
            "next": 0xB0,
            "previous": 0xB1,
            "stop": 0xB2,
        }
        vk_code = vk_map.get(key)
        if vk_code is None:
            return
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)

    def _extract_amount(self, text: str, default: int) -> int:
        numbers = re.findall(r"\d+", text)
        return int(numbers[0]) if numbers else default
