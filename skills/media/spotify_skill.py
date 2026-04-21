"""Spotify control skill backed by Spotipy."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any, ClassVar

from core.config import AppSettings
from core.error_telemetry import ErrorTelemetry
from core.models import Intent, IntentCategory, RequestContext, SkillResult
from core.runtime_events import RuntimeEventBroker
from skills.base_skill import BaseSkill


class SpotifySkill(BaseSkill):
    """Control Spotify playback using the Web API."""

    name: ClassVar[str] = "spotify"
    description: ClassVar[str] = "Control playback, search tracks, and inspect current music."
    triggers: ClassVar[list[str]] = ["spotify", "tocar musica", "play playlist", "pause spotify"]

    def __init__(
        self,
        settings: AppSettings,
        event_broker: RuntimeEventBroker,
        error_telemetry: ErrorTelemetry,
    ) -> None:
        super().__init__()
        self._settings = settings
        self._event_broker = event_broker
        self._error_telemetry = error_telemetry
        self._client: Any | None = None

    async def can_handle(self, intent: Intent) -> float:
        lowered_text = intent.raw_text.lower()
        if intent.category is IntentCategory.SPOTIFY:
            return 0.95
        if any(token in lowered_text for token in ["spotify", "pause", "pausa", "next", "proxima"]):
            return 0.72
        return 0.0

    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        command_name, query, volume = _extract_spotify_command(intent=intent)
        try:
            spotify_client = await asyncio.to_thread(self._get_client)
            result_payload = await asyncio.to_thread(
                self._run_command,
                spotify_client,
                command_name,
                query,
                volume,
            )
            await self._event_broker.publish(
                "activity",
                {"component": self.name, "message": result_payload["message"]},
            )
            return SkillResult(
                skill_name=self.name,
                success=True,
                message=str(result_payload["message"]),
                data=result_payload,
            )
        except Exception as exc:  # pragma: no cover
            await self._error_telemetry.record(
                component=self.name,
                error=type(exc).__name__,
                message=str(exc),
                metadata={"command_name": command_name, "query": query},
            )
            return SkillResult(
                skill_name=self.name,
                success=False,
                message=(
                    "Spotify control failed safely. "
                    "Check local credentials and playback state."
                ),
            )

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client

        import spotipy  # type: ignore[import-untyped]
        from spotipy.cache_handler import CacheFileHandler  # type: ignore[import-untyped]
        from spotipy.oauth2 import SpotifyOAuth, SpotifyPKCE  # type: ignore[import-untyped]

        token_path = Path(self._settings.spotify.token_path)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        cache_handler = CacheFileHandler(cache_path=str(token_path))

        if self._settings.env.spotify_client_secret:
            auth_manager = SpotifyOAuth(
                client_id=self._settings.env.spotify_client_id,
                client_secret=self._settings.env.spotify_client_secret,
                redirect_uri=self._settings.env.spotify_redirect_uri,
                scope=" ".join(self._settings.spotify.scopes),
                cache_handler=cache_handler,
                open_browser=True,
            )
        else:
            auth_manager = SpotifyPKCE(
                client_id=self._settings.env.spotify_client_id,
                redirect_uri=self._settings.env.spotify_redirect_uri,
                scope=" ".join(self._settings.spotify.scopes),
                cache_handler=cache_handler,
                open_browser=True,
            )

        self._client = spotipy.Spotify(auth_manager=auth_manager)
        return self._client

    def _run_command(
        self,
        spotify_client: Any,
        command_name: str,
        query: str | None,
        volume: int | None,
    ) -> dict[str, Any]:
        if command_name == "pause":
            spotify_client.pause_playback()
            return {"message": "Spotify playback paused.", "command_name": command_name}
        if command_name == "next":
            spotify_client.next_track()
            return {"message": "Skipped to the next Spotify track.", "command_name": command_name}
        if command_name == "previous":
            spotify_client.previous_track()
            return {
                "message": "Went back to the previous Spotify track.",
                "command_name": command_name,
            }
        if command_name == "volume" and volume is not None:
            spotify_client.volume(volume)
            return {
                "message": f"Spotify volume set to {volume} percent.",
                "command_name": command_name,
                "volume": volume,
            }
        if command_name == "current_track":
            current_track = spotify_client.current_user_playing_track()
            item = current_track.get("item", {}) if current_track else {}
            artist_names = ", ".join(artist["name"] for artist in item.get("artists", []))
            track_name = item.get("name", "unknown track")
            return {
                "message": f"Currently playing {track_name} by {artist_names}.",
                "command_name": command_name,
                "track": item,
            }

        search_query = query or "lofi"
        search_results = spotify_client.search(search_query, limit=1, type="track")
        items = search_results.get("tracks", {}).get("items", [])
        if not items:
            raise ValueError(f"No Spotify results were found for '{search_query}'.")
        track = items[0]
        spotify_client.start_playback(uris=[track["uri"]])
        artist_names = ", ".join(artist["name"] for artist in track.get("artists", []))
        return {
            "message": f"Playing {track['name']} by {artist_names}.",
            "command_name": "search_and_play",
            "track": track,
        }


def _extract_spotify_command(intent: Intent) -> tuple[str, str | None, int | None]:
    query = intent.entities.get("query")
    lowered_text = intent.raw_text.lower()
    if any(token in lowered_text for token in ["pause", "pausa"]):
        return "pause", query, None
    if any(token in lowered_text for token in ["proxima", "next"]):
        return "next", query, None
    if any(token in lowered_text for token in ["anterior", "previous"]):
        return "previous", query, None
    if any(token in lowered_text for token in ["tocando", "current track", "musica atual"]):
        return "current_track", query, None
    volume_match = re.search(r"volume\s+(\d{1,3})", lowered_text)
    if volume_match is not None:
        bounded_volume = min(100, max(0, int(volume_match.group(1))))
        return "volume", query, bounded_volume

    cleaned_query = query or re.sub(
        r"^(spotify|toque|tocar|play)\s+",
        "",
        intent.raw_text,
        flags=re.IGNORECASE,
    ).strip()
    return "search_and_play", cleaned_query or "lofi", None
