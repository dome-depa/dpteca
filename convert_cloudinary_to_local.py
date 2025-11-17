#!/usr/bin/env python
"""
Script per convertire URL Cloudinary in percorsi locali nel database.
Esegue la ricerca dei file locali e aggiorna il database con i percorsi relativi.
"""
import os
import sys
import django
from pathlib import Path
from django.utils.text import slugify

# Configurazione Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from music.models import Artista, Album
from django.conf import settings

def find_local_image(base_paths, filename_variations):
    """
    Cerca un'immagine locale tra i percorsi base e le variazioni del nome file.
    Restituisce il percorso relativo a MEDIA_ROOT se trovato, altrimenti None.
    """
    media_root = Path(settings.MEDIA_ROOT)
    
    for base_path in base_paths:
        for filename_var in filename_variations:
            full_path = media_root / base_path / filename_var
            if full_path.exists():
                # Restituisce il percorso relativo a MEDIA_ROOT
                relative_path = Path(base_path) / filename_var
                return str(relative_path)
    
    # Cerca anche nella root di media-serve
    for filename_var in filename_variations:
        full_path = media_root / filename_var
        if full_path.exists():
            return filename_var
    
    return None

def convert_artista_photos():
    """Converte le foto degli artisti da URL Cloudinary a percorsi locali."""
    artisti = Artista.objects.exclude(foto_artista='').exclude(foto_artista__isnull=True)
    converted = 0
    not_found = 0
    
    print(f"Trovati {artisti.count()} artisti con foto...")
    
    for artista in artisti:
        foto_url = artista.foto_artista.name if hasattr(artista.foto_artista, 'name') else str(artista.foto_artista)
        
        # Se non è un URL Cloudinary, salta
        if not foto_url.startswith('http'):
            print(f"  ✓ {artista.nome_artista}: già locale ({foto_url})")
            continue
        
        # Estrai il nome file dall'URL Cloudinary
        # Es: https://res.cloudinary.com/.../artisti/The_Beatles.jpg -> The_Beatles.jpg
        filename_from_url = Path(foto_url).name
        
        # Genera variazioni del nome file
        nome_slug = slugify(artista.nome_artista)
        filename_variations = [
            filename_from_url,  # Nome esatto dall'URL
            f"{artista.nome_artista}.jpg",
            f"{artista.nome_artista}.jpeg",
            f"{artista.nome_artista}.png",
            f"{nome_slug}.jpg",
            f"{nome_slug}.jpeg",
            f"{nome_slug}.png",
            filename_from_url.replace('_', ' '),  # Con spazi invece di underscore
        ]
        
        # Cerca nelle directory possibili
        base_paths = ['artisti', 'Immagini/Artisti']
        local_path = find_local_image(base_paths, filename_variations)
        
        if local_path:
            artista.foto_artista = local_path
            artista.save(update_fields=['foto_artista'])
            converted += 1
            print(f"  ✓ {artista.nome_artista}: convertito -> {local_path}")
        else:
            not_found += 1
            print(f"  ✗ {artista.nome_artista}: file locale non trovato (URL: {foto_url})")
    
    print(f"\nArtisti: {converted} convertiti, {not_found} non trovati")
    return converted, not_found

def convert_album_covers():
    """Converte le copertine degli album da URL Cloudinary a percorsi locali."""
    albums = Album.objects.exclude(copertina='').exclude(copertina__isnull=True)
    converted = 0
    not_found = 0
    
    print(f"\nTrovati {albums.count()} album con copertina...")
    
    for album in albums:
        copertina_url = album.copertina.name if hasattr(album.copertina, 'name') else str(album.copertina)
        
        # Se non è un URL Cloudinary, salta
        if not copertina_url.startswith('http'):
            print(f"  ✓ {album.titolo_album}: già locale ({copertina_url})")
            continue
        
        # Estrai il nome file dall'URL Cloudinary
        filename_from_url = Path(copertina_url).name
        
        # Genera variazioni del nome file
        # Gli album potrebbero avere nomi come "The_Beatles_Abbey_Road.jpg"
        # o potrebbero essere numerati come "100_atom-heart-mother.png"
        artista_slug = slugify(album.artista_appartenenza.nome_artista)
        album_slug = slugify(album.titolo_album)
        
        filename_variations = [
            filename_from_url,  # Nome esatto dall'URL
            f"{album.titolo_album}.jpg",
            f"{album.titolo_album}.jpeg",
            f"{album.titolo_album}.png",
            f"{album_slug}.jpg",
            f"{album_slug}.jpeg",
            f"{album_slug}.png",
            f"{artista_slug}_{album_slug}.jpg",
            f"{artista_slug}_{album_slug}.jpeg",
            f"{artista_slug}_{album_slug}.png",
            filename_from_url.replace('_', ' '),  # Con spazi invece di underscore
        ]
        
        # Cerca nelle directory possibili
        base_paths = ['album_covers', 'Immagini/Album']
        local_path = find_local_image(base_paths, filename_variations)
        
        if local_path:
            album.copertina = local_path
            album.save(update_fields=['copertina'])
            converted += 1
            print(f"  ✓ {album.titolo_album}: convertito -> {local_path}")
        else:
            not_found += 1
            print(f"  ✗ {album.titolo_album}: file locale non trovato (URL: {copertina_url})")
    
    print(f"\nAlbum: {converted} convertiti, {not_found} non trovati")
    return converted, not_found

if __name__ == '__main__':
    print("=" * 60)
    print("Conversione URL Cloudinary -> Percorsi Locali")
    print("=" * 60)
    
    if not settings.MEDIA_ROOT:
        print("ERRORE: MEDIA_ROOT non configurato!")
        sys.exit(1)
    
    print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print()
    
    # Converti foto artisti
    artisti_conv, artisti_not = convert_artista_photos()
    
    # Converti copertine album
    albums_conv, albums_not = convert_album_covers()
    
    print("\n" + "=" * 60)
    print("RIEPILOGO:")
    print(f"  Artisti convertiti: {artisti_conv}")
    print(f"  Artisti non trovati: {artisti_not}")
    print(f"  Album convertiti: {albums_conv}")
    print(f"  Album non trovati: {albums_not}")
    print("=" * 60)

