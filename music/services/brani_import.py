from dataclasses import dataclass

from django.db import transaction

from music.models import Album, Brano
from music.services.musicbrainz import TrackCandidate


@dataclass
class ImportResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0


def import_tracks_for_album(
    album: Album,
    tracks: list[TrackCandidate],
    *,
    skip_existing: bool = True,
    update_existing: bool = False,
) -> ImportResult:
    result = ImportResult()

    for track in tracks:
        existing = Brano.objects.filter(
            album_appartenenza=album,
            titolo_brano__iexact=track.titolo_brano,
        ).first()

        if existing:
            if skip_existing and not update_existing:
                result.skipped += 1
                continue
            brano = existing
            action = "updated"
        else:
            brano = Brano(album_appartenenza=album)
            action = "created"

        brano.titolo_brano = track.titolo_brano
        brano.sezione = track.sezione
        brano.progressivo = track.progressivo
        brano.durata = track.durata
        brano.crediti = track.crediti

        with transaction.atomic():
            brano.save()

        if action == "created":
            result.created += 1
        else:
            result.updated += 1

    return result
