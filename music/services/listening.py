from typing import Optional
from urllib.parse import quote_plus

import requests
from django.conf import settings

from music.models import Brano

REQUEST_TIMEOUT = 15


def _user_agent() -> str:
    return getattr(
        settings,
        "MUSICBRAINZ_USER_AGENT",
        "DPTeca/1.0 (https://dpteca.casanausicaa.it)",
    )


def _youtube_api_key() -> str:
    return (getattr(settings, "YOUTUBE_API_KEY", None) or "").strip()


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


def find_youtube_watch_url(artist: str, album: str, track: str) -> Optional[str]:
    """
    Cerca il primo video YouTube pertinente via Data API.
    Richiede YOUTUBE_API_KEY; senza chiave restituisce None.
    """
    api_key = _youtube_api_key()
    if not api_key:
        return None

    query = f"{artist} {album} {track}".strip()
    try:
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "type": "video",
                "maxResults": 1,
                "q": query,
                "key": api_key,
            },
            headers={
                "User-Agent": _user_agent(),
                "Accept": "application/json",
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return None

    items = payload.get("items") or []
    if not items:
        return None
    video_id = (items[0].get("id") or {}).get("videoId")
    if not video_id:
        return None
    return f"https://www.youtube.com/watch?v={video_id}"


def is_cacheable_listen_url(url: str, source: str) -> bool:
    if not url:
        return False
    if source == Brano.ASCOLTO_FONTE_BANDCAMP:
        return "bandcamp.com" in url
    if source == Brano.ASCOLTO_FONTE_YOUTUBE:
        return "youtube.com/watch" in url or "youtu.be/" in url
    return False


def cache_listen_url(brano: Brano, url: str, source: str) -> None:
    if not is_cacheable_listen_url(url, source):
        return
    if brano.ascolto_url == url and brano.ascolto_fonte == source:
        return
    brano.ascolto_url = url
    brano.ascolto_fonte = source
    brano.save(update_fields=["ascolto_url", "ascolto_fonte"])


def resolve_listen_url(
    brano: Brano,
    *,
    refresh: bool = False,
) -> tuple[str, str, bool]:
    """
    Restituisce (url, fonte, from_cache).
    Ordine: cache → Bandcamp → YouTube watch (API) → YouTube search.
    """
    if not refresh and brano.ascolto_url and brano.ascolto_fonte:
        return brano.ascolto_url, brano.ascolto_fonte, True

    album = brano.album_appartenenza
    artista = album.artista_appartenenza
    artist_name = artista.nome_artista
    album_title = album.titolo_album
    track_title = brano.titolo_brano

    bandcamp_url = find_bandcamp_url(artist_name, album_title, track_title)
    if bandcamp_url:
        cache_listen_url(brano, bandcamp_url, Brano.ASCOLTO_FONTE_BANDCAMP)
        return bandcamp_url, Brano.ASCOLTO_FONTE_BANDCAMP, False

    youtube_watch = find_youtube_watch_url(artist_name, album_title, track_title)
    if youtube_watch:
        cache_listen_url(brano, youtube_watch, Brano.ASCOLTO_FONTE_YOUTUBE)
        return youtube_watch, Brano.ASCOLTO_FONTE_YOUTUBE, False

    return (
        youtube_search_url(artist_name, album_title, track_title),
        Brano.ASCOLTO_FONTE_YOUTUBE,
        False,
    )


def find_listen_url(artist: str, album: str, track: str) -> tuple[str, str]:
    """
    Restituisce (url, fonte) con fonte 'bandcamp' o 'youtube'.
    """
    bandcamp_url = find_bandcamp_url(artist, album, track)
    if bandcamp_url:
        return bandcamp_url, Brano.ASCOLTO_FONTE_BANDCAMP

    youtube_watch = find_youtube_watch_url(artist, album, track)
    if youtube_watch:
        return youtube_watch, Brano.ASCOLTO_FONTE_YOUTUBE

    return youtube_search_url(artist, album, track), Brano.ASCOLTO_FONTE_YOUTUBE
