from dataclasses import dataclass

from django.db import transaction

from music.models import Album, Brano
from music.services.musicbrainz import TrackCandidate


@dataclass
class ImportResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0


def _apply_track_position(brano: Brano, track: TrackCandidate) -> bool:
    changed = False
    if brano.sezione != track.sezione:
        brano.sezione = track.sezione
        changed = True
    if brano.progressivo != track.progressivo:
        brano.progressivo = track.progressivo
        changed = True
    return changed


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
            brano = existing
            position_changed = _apply_track_position(brano, track)
            metadata_changed = False

            if update_existing or not skip_existing:
                if brano.titolo_brano != track.titolo_brano:
                    brano.titolo_brano = track.titolo_brano
                    metadata_changed = True
                if brano.durata != track.durata:
                    brano.durata = track.durata
                    metadata_changed = True
                if brano.crediti != track.crediti:
                    brano.crediti = track.crediti
                    metadata_changed = True

            if position_changed or metadata_changed:
                with transaction.atomic():
                    brano.save()
                result.updated += 1
            else:
                result.skipped += 1
            continue

        brano = Brano(
            album_appartenenza=album,
            titolo_brano=track.titolo_brano,
            sezione=track.sezione,
            progressivo=track.progressivo,
            durata=track.durata,
            crediti=track.crediti,
        )
        with transaction.atomic():
            brano.save()
        result.created += 1

    return result
