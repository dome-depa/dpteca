from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from music.models import Artista


class Command(BaseCommand):
    help = (
        "Associa le immagini degli artisti usando i file presenti nella "
        "directory Immagini/Artisti (il nome del file deve corrispondere al nome dell'artista)"
    )

    SUPPORTED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif", ".webp"]

    def add_arguments(self, parser):
        parser.add_argument(
            "--images-dir",
            type=str,
            default="Immagini/Artisti",
            help="Directory contenente le immagini (default: Immagini/Artisti)",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Sovrascrive le foto già presenti",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Elimina tutte le foto esistenti prima di ricaricarle",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limita il numero di artisti processati",
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

    def _find_image_for_artista(self, base_dir: Path, nome: str) -> Path | None:
        if not nome:
            return None

        # Normalizza il nome per la ricerca (rimuovi caratteri problematici)
        def normalize_for_search(text):
            # Sostituisci caratteri comuni che possono variare
            text = text.replace('/', ' ').replace(':', ' ').replace('-', ' ')
            text = text.replace('"', '').replace("'", "").replace('…', '')
            # Rimuovi spazi multipli
            text = ' '.join(text.split())
            return text.strip().lower()

        nome_normalized = normalize_for_search(nome)

        # Prova prima con il nome esatto
        for ext in self.SUPPORTED_EXTENSIONS:
            candidate = base_dir / f"{nome}{ext}"
            if candidate.exists():
                return candidate
        
        # Se non trovato, cerca tra tutti i file normalizzando i nomi
        for file_path in base_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                file_name_normalized = normalize_for_search(file_path.stem)
                # Confronta i nomi normalizzati
                if file_name_normalized == nome_normalized:
                    return file_path
                # Prova anche se il nome è contenuto nel nome del file o viceversa
                if nome_normalized in file_name_normalized or file_name_normalized in nome_normalized:
                    # Verifica che la corrispondenza sia significativa (almeno 3 caratteri)
                    if len(nome_normalized) >= 3 or len(file_name_normalized) >= 3:
                        return file_path
        
        return None

    def handle(self, *args, **options):
        images_dir = self._resolve_dir(options["images_dir"])
        overwrite = options["overwrite"]
        clear = options["clear"]
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

        # Elimina tutte le foto esistenti se richiesto
        if clear:
            if dry_run:
                self.stdout.write(self.style.WARNING("[DRY RUN] Eliminerei tutte le foto esistenti"))
            else:
                cleared = Artista.objects.exclude(foto_artista='').exclude(foto_artista__isnull=True).count()
                Artista.objects.all().update(foto_artista='')
                self.stdout.write(self.style.SUCCESS(f"Eliminate {cleared} foto esistenti"))

        artisti = Artista.objects.all().order_by("pk")
        if limit:
            artisti = artisti[:limit]

        total = artisti.count()
        self.stdout.write(f"Artisti da processare: {total}")

        updated = 0
        skipped_missing = 0
        skipped_existing = 0
        errors = 0
        preview = 0

        for artista in artisti:
            image_path = self._find_image_for_artista(images_dir, artista.nome_artista)
            if not image_path:
                skipped_missing += 1
                continue

            if artista.foto_artista and not overwrite and not clear:
                skipped_existing += 1
                continue

            if dry_run and preview < 5:
                self.stdout.write(
                    f"[Anteprima] {artista.nome_artista} <- {image_path.name}"
                )
                preview += 1

            if dry_run:
                updated += 1
                continue

            try:
                filename = (
                    f"artisti/{artista.pk}_"
                    f"{slugify(artista.nome_artista)}{image_path.suffix.lower()}"
                )
                with image_path.open("rb") as img_file:
                    artista.foto_artista.save(filename, File(img_file), save=True)
                updated += 1
            except Exception as exc:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Errore nel salvare {image_path.name} per '{artista.nome_artista}': {exc}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("AGGIORNAMENTO FOTO ARTISTI COMPLETATO"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"Artisti aggiornati: {updated}")
        self.stdout.write(f"Artisti saltati (foto già presente): {skipped_existing}")
        self.stdout.write(f"Artisti senza immagine corrispondente: {skipped_missing}")
        self.stdout.write(f"Errori: {errors}")

