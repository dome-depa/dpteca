import re
import time
from dataclasses import dataclass
from typing import Optional

import requests
from django.conf import settings

MUSICBRAINZ_API_URL = "https://musicbrainz.org/ws/2"
REQUEST_TIMEOUT = 15
_last_request_at = 0.0


class MusicBrainzError(Exception):
    """Errore durante la comunicazione con MusicBrainz."""


@dataclass(frozen=True)
class ReleaseCandidate:
    mbid: str
    title: str
    date: str
    country: str
    label: str
    track_count: int
    medium_count: int


@dataclass(frozen=True)
class TrackCandidate:
    titolo_brano: str
    sezione: Optional[str]
    progressivo: Optional[str]
    durata: Optional[str]
    crediti: Optional[str]


def _user_agent() -> str:
    return getattr(
        settings,
        "MUSICBRAINZ_USER_AGENT",
        "DPTeca/1.0 (https://github.com/dpteca)",
    )


def _escape_lucene(value: str) -> str:
    return re.sub(r'([+\-&|!(){}[\]^"~*?:\\/])', r"\\\1", value.strip())


def _throttle() -> None:
    global _last_request_at
    min_interval = 1.0
    elapsed = time.monotonic() - _last_request_at
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    _last_request_at = time.monotonic()


def _get(path: str, params: Optional[dict] = None) -> dict:
    _throttle()
    url = f"{MUSICBRAINZ_API_URL}/{path.lstrip('/')}"
    try:
        response = requests.get(
            url,
            params=params,
            headers={"User-Agent": _user_agent(), "Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise MusicBrainzError(f"Richiesta a MusicBrainz fallita: {exc}") from exc
    except ValueError as exc:
        raise MusicBrainzError("Risposta MusicBrainz non valida.") from exc


def format_duration(length_ms: Optional[int]) -> Optional[str]:
    if not length_ms:
        return None
    total_seconds = max(int(length_ms // 1000), 0)
    minutes, seconds = divmod(total_seconds, 60)
    formatted = f"{minutes}:{seconds:02d}"
    return formatted[:5]


def _release_label(release: dict) -> str:
    for label_info in release.get("label-info") or []:
        label = label_info.get("label") or {}
        name = (label.get("name") or "").strip()
        if name:
            return name
    return ""


def search_releases(
    artist_name: str,
    album_title: str,
    release_date: Optional[str] = None,
    limit: int = 10,
) -> list[ReleaseCandidate]:
    artist = _escape_lucene(artist_name)
    album = _escape_lucene(album_title)
    query_parts = [f'artist:"{artist}"', f'release:"{album}"']
    if release_date:
        year = str(release_date)[:4]
        if year.isdigit():
            query_parts.append(f"date:{year}")
    payload = _get(
        "release",
        {
            "query": " AND ".join(query_parts),
            "fmt": "json",
            "limit": limit,
        },
    )
    candidates = []
    for release in payload.get("releases") or []:
        mbid = release.get("id")
        title = (release.get("title") or "").strip()
        if not mbid or not title:
            continue
        candidates.append(
            ReleaseCandidate(
                mbid=mbid,
                title=title,
                date=(release.get("date") or "").strip(),
                country=(release.get("country") or "").strip(),
                label=_release_label(release),
                track_count=int(release.get("track-count") or 0),
                medium_count=int(release.get("medium-count") or 0),
            )
        )
    return candidates


def get_release_tracks(release_mbid: str) -> list[TrackCandidate]:
    payload = _get(
        f"release/{release_mbid}",
        {"inc": "recordings+artist-credits+media", "fmt": "json"},
    )
    tracks: list[TrackCandidate] = []
    media_list = payload.get("media") or []
    single_medium = len(media_list) <= 1

    for medium in media_list:
        medium_position = int(medium.get("position") or 1)
        if single_medium:
            sezione = "a"
        else:
            sezione = chr(ord("a") + medium_position - 1)

        for track in medium.get("tracks") or []:
            title = (track.get("title") or "").strip()
            if not title:
                continue
            position = track.get("number") or track.get("position")
            progressivo = str(position).strip() if position is not None else None
            if progressivo:
                progressivo = progressivo[:3]

            recording = track.get("recording") or {}
            crediti = _recording_credits(recording)

            tracks.append(
                TrackCandidate(
                    titolo_brano=title[:150],
                    sezione=sezione[:2] if sezione else None,
                    progressivo=progressivo,
                    durata=format_duration(track.get("length") or recording.get("length")),
                    crediti=crediti[:100] if crediti else None,
                )
            )
    return tracks


def _recording_credits(recording: dict) -> Optional[str]:
    artist_credit = recording.get("artist-credit") or []
    names = []
    for entry in artist_credit:
        name = (entry.get("name") or "").strip()
        if name:
            names.append(name)
    if names:
        return ", ".join(names)
    return None
