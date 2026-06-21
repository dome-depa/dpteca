from typing import Optional
from urllib.parse import quote_plus

import requests
from django.conf import settings

REQUEST_TIMEOUT = 15


def _user_agent() -> str:
    return getattr(
        settings,
        "MUSICBRAINZ_USER_AGENT",
        "DPTeca/1.0 (https://dpteca.casanausicaa.it)",
    )


def find_bandcamp_url(artist: str, album: str, track: str) -> Optional[str]:
    query = f"{artist} {album} {track}".strip()
    try:
        response = requests.get(
            "https://bandcamp.com/api/fuzzysearch/1/app_autocomplete",
            params={"q": query, "item_type": "t"},
            headers={
                "User-Agent": _user_agent(),
                "Accept": "application/json",
                "Referer": "https://bandcamp.com/",
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        if "application/json" not in response.headers.get("Content-Type", ""):
            return None
        payload = response.json()
    except (requests.RequestException, ValueError):
        return None

    for result in payload.get("results") or []:
        if result.get("itemtype") == "t" and result.get("url"):
            return result["url"]
    return None


def youtube_search_url(artist: str, album: str, track: str) -> str:
    query = quote_plus(f"{artist} {album} {track}".strip())
    return f"https://www.youtube.com/results?search_query={query}"


def find_listen_url(artist: str, album: str, track: str) -> tuple[str, str]:
    """
    Restituisce (url, fonte) con fonte 'bandcamp' o 'youtube'.
    """
    bandcamp_url = find_bandcamp_url(artist, album, track)
    if bandcamp_url:
        return bandcamp_url, "bandcamp"
    return youtube_search_url(artist, album, track), "youtube"
