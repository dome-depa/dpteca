from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from music.models import Album


class Command(BaseCommand):
    help = (
        "Associa le immagini di copertina agli album usando i file presenti nella "
        "directory Immagini/Album (il nome del file deve corrispondere al titolo)"
    )

    SUPPORTED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif", ".webp"]

    def add_arguments(self, parser):
        parser.add_argument(
            "--images-dir",
            type=str,
            default="Immagini/Album",
            help="Directory contenente le immagini (default: Immagini/Album)",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Sovrascrive le copertine già presenti",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limita il numero di album processati",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostra cosa verrebbe fatto senza salvare nel database",
        )

    def _resolve_dir(self, images_dir: str) -> Path | None:
        dir_path = Path(images_dir)
        if dir_path.exists():
            return dir_path

        project_root = Path(__file__).resolve().parent.parent.parent.parent
        candidate = project_root / images_dir
        if candidate.exists():
            return candidate
        return None

    def _find_image_for_album(self, base_dir: Path, titolo: str) -> Path | None:
        if not titolo:
            return None

        for ext in self.SUPPORTED_EXTENSIONS:
            candidate = base_dir / f"{titolo}{ext}"
            if candidate.exists():
                return candidate
        return None

    def handle(self, *args, **options):
        images_dir = self._resolve_dir(options["images_dir"])
        overwrite = options["overwrite"]
        limit = options["limit"]
        dry_run = options["dry_run"]

        if not images_dir:
            self.stdout.write(
                self.style.ERROR(
                    f"Directory immagini non trovata: {options['images_dir']}"
                )
            )
            return

        self.stdout.write(f"Directory immagini: {images_dir}")

        albums = Album.objects.all().order_by("pk")
        if limit:
            albums = albums[:limit]

        total = albums.count()
        self.stdout.write(f"Album da processare: {total}")

        updated = 0
        skipped_missing = 0
        skipped_existing = 0
        errors = 0
        preview = 0

        for album in albums:
            image_path = self._find_image_for_album(images_dir, album.titolo_album)
            if not image_path:
                skipped_missing += 1
                continue

            if album.copertina and not overwrite:
                skipped_existing += 1
                continue

            if dry_run and preview < 5:
                self.stdout.write(
                    f"[Anteprima] {album.titolo_album} <- {image_path.name}"
                )
                preview += 1

            if dry_run:
                updated += 1
                continue

            try:
                filename = (
                    f"album_covers/{album.pk}_"
                    f"{slugify(album.titolo_album)}{image_path.suffix.lower()}"
                )
                with image_path.open("rb") as img_file:
                    album.copertina.save(filename, File(img_file), save=True)
                updated += 1
            except Exception as exc:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Errore nel salvare {image_path.name} per '{album.titolo_album}': {exc}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("AGGIORNAMENTO COPERTINE COMPLETATO"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"Album aggiornati: {updated}")
        self.stdout.write(f"Album saltati (copertina già presente): {skipped_existing}")
        self.stdout.write(f"Album senza immagine corrispondente: {skipped_missing}")
        self.stdout.write(f"Errori: {errors}")

