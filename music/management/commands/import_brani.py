import itertools
from collections import defaultdict
from pathlib import Path

import openpyxl
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from music.models import Album, Brano


class Command(BaseCommand):
    help = "Importa i brani dal file Excel Brani.xlsx"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="Brani.xlsx",
            help="Percorso del file Excel da importare (default: Brani.xlsx)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Numero massimo di righe da processare",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula l'import senza scrivere sul database",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Salta i brani già presenti (stesso titolo e album)",
        )
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Aggiorna i brani già presenti",
        )

    @staticmethod
    def _resolve_file(path):
        file_path = Path(path)
        if file_path.exists():
            return file_path
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        candidate = project_root / path
        if candidate.exists():
            return candidate
        return None

    @staticmethod
    def _clean(value):
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _find_album(self, titolo_album, artista_nome=None, artista_comp=None):
        if not titolo_album:
            return None

        base_qs = Album.objects.filter(titolo_album=titolo_album)

        if artista_nome:
            qs = base_qs.filter(artista_appartenenza__nome_artista=artista_nome)
            if qs.count() == 1:
                return qs.first()

        if artista_comp:
            qs = base_qs.filter(artista_appartenenza__nome_artista=artista_comp)
            if qs.count() == 1:
                return qs.first()

        if base_qs.count() == 1:
            return base_qs.first()

        return None

    def handle(self, *args, **options):
        file_path = self._resolve_file(options["file"])
        limit = options.get("limit")
        dry_run = options.get("dry_run")
        skip_existing = options.get("skip_existing")
        update_existing = options.get("update_existing")

        if skip_existing and update_existing:
            self.stdout.write(
                self.style.ERROR(
                    "Non è possibile usare contemporaneamente --skip-existing e --update-existing"
                )
            )
            return

        if not file_path:
            self.stdout.write(
                self.style.ERROR(f"File Excel non trovato: {options['file']}")
            )
            return

        self.stdout.write(f"Lettura file: {file_path}")
        workbook = openpyxl.load_workbook(file_path)
        worksheet = workbook.active
        self.stdout.write(f"Foglio: {worksheet.title}")

        rows = list(worksheet.iter_rows(values_only=True))
        if not rows:
            self.stdout.write(self.style.WARNING("Nessun dato trovato nel file"))
            return

        headers = [self._clean(col) for col in rows[0]]
        data_rows = rows[1:]
        if limit:
            data_rows = data_rows[:limit]

        self.stdout.write(f"Righe da processare: {len(data_rows)}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - nessun dato sarà scritto"))
            for idx, row in enumerate(itertools.islice(data_rows, 5), 1):
                data = dict(zip(headers, row))
                self.stdout.write(
                    f"[Anteprima {idx}] {data.get('Tracce')} "
                    f"({data.get('TitoloAlbum')} - {data.get('Artista')})"
                )
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0
        missing_album = 0
        errors = []

        # Mantiene il contatore progressivo per album (parte dal numero di brani già presenti)
        album_progressivi = defaultdict(int)
        existing_counts = (
            Brano.objects.values("album_appartenenza")
            .annotate(total=Count("id"))
        )
        for entry in existing_counts:
            album_progressivi[entry["album_appartenenza"]] = entry["total"] or 0

        for row in data_rows:
            data = dict(zip(headers, row))
            titolo_album = self._clean(data.get("TitoloAlbum"))
            artista_nome = self._clean(data.get("Artista"))
            artista_comp = self._clean(data.get("ArtistaCompilation"))
            titolo_brano = self._clean(data.get("Tracce"))

            if not titolo_brano or not titolo_album:
                skipped_count += 1
                continue

            album = self._find_album(titolo_album, artista_nome, artista_comp)
            if not album:
                missing_album += 1
                errors.append(
                    f"Album non trovato per '{titolo_brano}' "
                    f"({titolo_album} - {artista_nome or artista_comp})"
                )
                continue

            qs = Brano.objects.filter(titolo_brano=titolo_brano, album_appartenenza=album)
            if qs.exists():
                if skip_existing or not update_existing:
                    skipped_count += 1
                    continue
                brano = qs.first()
                action = "updated"
            else:
                brano = Brano(album_appartenenza=album)
                action = "created"

            album_progressivi.setdefault(album.pk, album.brani.count())
            album_progressivi[album.pk] += 1
            progressivo = album_progressivi[album.pk]

            brano.titolo_brano = titolo_brano[: Brano._meta.get_field("titolo_brano").max_length]
            max_prog_len = Brano._meta.get_field("progressivo").max_length
            brano.progressivo = str(progressivo).zfill(max_prog_len)
            brano.sezione = None
            brano.crediti = None
            brano.durata = None

            try:
                with transaction.atomic():
                    brano.save()
                if action == "created":
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as exc:
                errors.append(f"Errore con '{titolo_brano}': {exc}")
                skipped_count += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("IMPORTAZIONE BRANI COMPLETATA"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"Brani creati: {created_count}")
        self.stdout.write(f"Brani aggiornati: {updated_count}")
        self.stdout.write(f"Brani saltati: {skipped_count}")
        self.stdout.write(f"Brani senza album associato: {missing_album}")
        self.stdout.write(f"Totale brani nel database: {Brano.objects.count()}")

        if errors:
            self.stdout.write(self.style.ERROR("Dettaglio errori:"))
            for err in errors[:20]:
                self.stdout.write(self.style.ERROR(f" - {err}"))
            if len(errors) > 20:
                self.stdout.write(self.style.ERROR(f"... altri {len(errors) - 20} errori"))

