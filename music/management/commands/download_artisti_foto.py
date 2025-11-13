from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from music.models import Artista
from PIL import Image
import requests
from io import BytesIO
import time
import os
from pathlib import Path
import urllib.parse


class Command(BaseCommand):
    help = 'Scarica e carica le foto degli artisti da internet'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limita il numero di artisti da processare'
        )
        parser.add_argument(
            '--max-size',
            type=int,
            default=500,
            help='Dimensione massima dell\'immagine in pixel (default: 500)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=3.0,
            help='Ritardo tra le richieste in secondi (default: 3.0)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula senza scaricare realmente le immagini'
        )
        parser.add_argument(
            '--api-key',
            type=str,
            default=None,
            help='Chiave API Pixabay (opzionale, ottieni gratuita su https://pixabay.com/api/docs/)'
        )

    def download_image(self, url, max_size=500):
        """Scarica e ridimensiona un'immagine da un URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10, stream=True)
            response.raise_for_status()
            
            # Verifica che sia un'immagine
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return None
            
            # Carica l'immagine
            img = Image.open(BytesIO(response.content))
            
            # Converti in RGB se necessario (per JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Crea uno sfondo bianco per immagini con trasparenza
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Ridimensiona mantenendo le proporzioni
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Salva in memoria
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            return output
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"Errore nel download da {url}: {str(e)}")
            )
            return None

    def search_artist_image(self, artist_name, api_key=None):
        """Cerca un'immagine per un artista usando Pixabay API o fallback"""
        # Prova prima con Pixabay se la chiave è disponibile
        if api_key:
            try:
                query = urllib.parse.quote(f"{artist_name} musician")
                url = f"https://pixabay.com/api/?key={api_key}&q={query}&image_type=photo&category=music&safesearch=true&per_page=5"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data.get('totalHits', 0) > 0:
                    # Prova a scaricare la prima immagine valida
                    for hit in data.get('hits', [])[:3]:
                        img_url = hit.get('webformatURL') or hit.get('largeImageURL')
                        if img_url:
                            img_data = self.download_image(img_url)
                            if img_data:
                                return img_data
            except Exception as e:
                pass  # Fallback a metodo alternativo
        
        # Fallback: usa DuckDuckGo con delay maggiore
        return self.search_google_images(artist_name)
    
    def search_google_images(self, artist_name):
        """Fallback: cerca immagini usando ricerca Google diretta"""
        try:
            # Usa DuckDuckGo come fallback con delay maggiore
            from duckduckgo_search import DDGS
            
            query = f"{artist_name} musician band artist photo"
            time.sleep(5)  # Delay maggiore per evitare rate limit
            
            with DDGS() as ddgs:
                results = list(ddgs.images(
                    query,
                    max_results=3,
                    safesearch='moderate'
                ))
            
            if not results:
                return None
            
            # Prova a scaricare la prima immagine valida
            for result in results:
                url = result.get('image')
                if url:
                    img_data = self.download_image(url)
                    if img_data:
                        return img_data
            
            return None
            
        except Exception as e:
            return None

    def handle(self, *args, **options):
        limit = options['limit']
        max_size = options['max_size']
        delay = options['delay']
        dry_run = options['dry_run']
        api_key = options.get('api_key')
        
        # Se non c'è chiave API, avvisa l'utente
        if not api_key:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  Nessuna chiave API Pixabay fornita.\n'
                    '   Per risultati migliori, ottieni una chiave gratuita su:\n'
                    '   https://pixabay.com/api/docs/\n'
                    '   E usa: --api-key TUA_CHIAVE\n'
                    '   Continuo con metodo alternativo (più lento)...\n'
                )
            )
        
        # Trova artisti senza foto
        artisti_senza_foto = Artista.objects.filter(
            foto_artista__isnull=True
        ) | Artista.objects.filter(foto_artista='')
        
        if limit:
            artisti_senza_foto = artisti_senza_foto[:limit]
        
        total = artisti_senza_foto.count()
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('Tutti gli artisti hanno già una foto!'))
            return
        
        self.stdout.write(f'Trovati {total} artisti senza foto')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - Nessuna immagine verrà scaricata'))
            for artista in artisti_senza_foto:
                self.stdout.write(f'  - {artista.nome_artista}')
            return
        
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for i, artista in enumerate(artisti_senza_foto, 1):
            self.stdout.write(f'\n[{i}/{total}] Processando: {artista.nome_artista}...')
            
            # Cerca e scarica l'immagine
            img_data = self.search_artist_image(artista.nome_artista, api_key=api_key)
            
            if img_data:
                try:
                    # Genera nome file
                    safe_name = "".join(c for c in artista.nome_artista if c.isalnum() or c in (' ', '-', '_')).strip()
                    safe_name = safe_name.replace(' ', '_')
                    filename = f'artisti/{safe_name}.jpg'
                    
                    # Salva l'immagine
                    artista.foto_artista.save(
                        filename,
                        ContentFile(img_data.read()),
                        save=True
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Foto scaricata e salvata: {filename}')
                    )
                    success_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Errore nel salvataggio: {str(e)}')
                    )
                    error_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠ Nessuna immagine trovata per {artista.nome_artista}')
                )
                skipped_count += 1
            
            # Ritardo tra le richieste per evitare rate limiting
            if i < total:
                time.sleep(delay)
        
        # Riepilogo
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('SCARICAMENTO COMPLETATO'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'Foto scaricate con successo: {success_count}')
        self.stdout.write(f'Foto non trovate: {skipped_count}')
        self.stdout.write(f'Errori: {error_count}')
        self.stdout.write(f'Totale processati: {total}')
        self.stdout.write('')

