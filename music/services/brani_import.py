from dataclasses import dataclass

from django.db import transaction

from music.models import Album, Brano
from music.services.musicbrainz import TrackCandidate


@dataclass
class ImportResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0


def _is_empty(value: str | None) -> bool:
    return value is None or not str(value).strip()


def _apply_track_position(brano: Brano, track: TrackCandidate) -> bool:
    changed = False
    if brano.sezione != track.sezione:
        brano.sezione = track.sezione
        changed = True
    if brano.progressivo != track.progressivo:
        brano.progressivo = track.progressivo
        changed = True
    return changed


def _apply_track_metadata(
    brano: Brano,
    track: TrackCandidate,
    *,
    fill_missing: bool,
    overwrite: bool,
) -> bool:
    changed = False

    if overwrite:
        if brano.titolo_brano != track.titolo_brano:
            brano.titolo_brano = track.titolo_brano
            changed = True
        if brano.durata != track.durata:
            brano.durata = track.durata
            changed = True
        if brano.crediti != track.crediti:
            brano.crediti = track.crediti
            changed = True
        return changed

    if not fill_missing:
        return False

    if _is_empty(brano.durata) and not _is_empty(track.durata):
        brano.durata = track.durata
        changed = True
    if _is_empty(brano.crediti) and not _is_empty(track.crediti):
        brano.crediti = track.crediti
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
            metadata_changed = _apply_track_metadata(
                brano,
                track,
                fill_missing=True,
                overwrite=update_existing or not skip_existing,
            )

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
