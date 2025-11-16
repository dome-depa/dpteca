"""
Comando per caricare dati iniziali dal file data_export.json
Utile per popolare il database su Render dopo il deploy
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Carica dati iniziali dal file data_export.json'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data_export.json',
            help='Percorso del file JSON da caricare',
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        # Cerca il file nella directory del progetto
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        json_file = base_dir / file_path
        
        if not json_file.exists():
            self.stdout.write(
                self.style.WARNING(f'File {json_file} non trovato. Salto il caricamento dati.')
            )
            return
        
        self.stdout.write(f'Caricamento dati da {json_file}...')
        
        try:
            call_command('loaddata', str(json_file), verbosity=1)
            self.stdout.write(
                self.style.SUCCESS('Dati caricati con successo!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Errore durante il caricamento: {e}')
            )

