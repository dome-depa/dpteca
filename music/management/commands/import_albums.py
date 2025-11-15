import datetime
from pathlib import Path

import openpyxl
from django.core.management.base import BaseCommand
from django.db import transaction

from music.models import Album, Artista, Stile


class Command(BaseCommand):
    help = "Importa gli album dal file Excel DatiMusica.xlsx"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="DatiMusica.xlsx",
            help="Percorso del file Excel da importare (default: DatiMusica.xlsx)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Numero massimo di righe da importare",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Esegue l'analisi senza scrivere sul database",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Salta gli album già presenti (titolo + artista)",
        )
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Aggiorna gli album già presenti con i dati Excel",
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
    def _clean_string(value):
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _truncate(value, max_length):
        if value is None:
            return None
        value = str(value)
        return value[:max_length]

    @staticmethod
    def _parse_date(value):
        if not value:
            return None

        if isinstance(value, datetime.datetime):
            return value.date()
        if isinstance(value, datetime.date):
            return value
        if isinstance(value, (int, float)) and value > 999:
            try:
                return datetime.date(int(value), 1, 1)
            except ValueError:
                return None
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            if value.isdigit() and len(value) == 4:
                try:
                    return datetime.date(int(value), 1, 1)
                except ValueError:
                    return None
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                try:
                    return datetime.datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        return None

    @staticmethod
    def _parse_float(value):
        if value in (None, ""):
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _parse_bool(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(int(value))
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "si", "sì", "y", "yes"}
        return False

    @staticmethod
    def _parse_stili(value):
        if not value:
            return []
        if isinstance(value, str):
            separators = ["/", ",", ";", "|"]
            for sep in separators:
                if sep in value:
                    return [part.strip() for part in value.split(sep) if part.strip()]
            return [value.strip()]
        return [str(value).strip()]

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

        headers = [self._clean_string(col) for col in rows[0]]
        data_rows = rows[1:]
        if limit:
            data_rows = data_rows[:limit]

        total_rows = len(data_rows)
        self.stdout.write(f"Righe da processare: {total_rows}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - nessun dato sarà scritto"))
            preview = min(5, total_rows)
            for idx, row in enumerate(data_rows[:preview], 1):
                data = dict(zip(headers, row))
                self.stdout.write(
                    f"[Anteprima {idx}] {data.get('titolo_album')} - "
                    f"{data.get('artista_appartenenza')}"
                )
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        for idx, row in enumerate(data_rows, 1):
            data = dict(zip(headers, row))
            titolo = self._clean_string(data.get("titolo_album"))
            artista_nome = self._clean_string(data.get("artista_appartenenza"))

            if not titolo or not artista_nome:
                skipped_count += 1
                continue

            try:
                with transaction.atomic():
                    artista, _ = Artista.objects.get_or_create(
                        nome_artista=artista_nome
                    )

                    album_qs = Album.objects.filter(
                        titolo_album=titolo, artista_appartenenza=artista
                    )

                    if album_qs.exists():
                        if skip_existing:
                            skipped_count += 1
                            continue
                        album = album_qs.first()
                        action = "updated" if update_existing else "existing"
                    else:
                        album = Album(titolo_album=titolo, artista_appartenenza=artista)
                        action = "created"

                    if action == "existing" and not update_existing:
                        skipped_count += 1
                        continue

                    album.editore = self._truncate(
                        data.get("editore"),
                        Album._meta.get_field("editore").max_length,
                    )
                    album.catalogo = self._truncate(
                        data.get("catalogo"),
                        Album._meta.get_field("catalogo").max_length,
                    )
                    album.supporto = self._truncate(
                        data.get("supporto"),
                        Album._meta.get_field("supporto").max_length,
                    )
                    album.deposito = self._truncate(
                        data.get("deposito"),
                        Album._meta.get_field("deposito").max_length,
                    )
                    album.note = self._clean_string(data.get("note"))
                    album.costo = self._parse_float(data.get("costo"))
                    album.closed = self._parse_bool(data.get("closed"))
                    album.data_rilascio = self._parse_date(data.get("data_rilascio"))

                    stili_list = self._parse_stili(data.get("stili"))
                    album.genere = (
                        self._truncate(
                            stili_list[0],
                            Album._meta.get_field("genere").max_length,
                        )
                        if stili_list
                        else None
                    )

                    album.save()

                    if stili_list:
                        stile_objs = []
                        for stile_name in stili_list:
                            stile_obj, _ = Stile.objects.get_or_create(
                                stile=self._truncate(
                                    stile_name,
                                    Stile._meta.get_field("stile").max_length,
                                )
                            )
                            stile_objs.append(stile_obj)
                        album.stili.set(stile_objs)

                    if action == "created":
                        created_count += 1
                    else:
                        updated_count += 1

            except Exception as exc:
                errors.append(f"{titolo} - {artista_nome}: {exc}")
                skipped_count += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("IMPORTAZIONE ALBUM COMPLETATA"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"Album creati: {created_count}")
        self.stdout.write(f"Album aggiornati: {updated_count}")
        self.stdout.write(f"Album saltati: {skipped_count}")
        self.stdout.write(f"Totale album nel database: {Album.objects.count()}")

        if errors:
            self.stdout.write(self.style.ERROR("Errori riscontrati:"))
            for err in errors:
                self.stdout.write(self.style.ERROR(f" - {err}"))

