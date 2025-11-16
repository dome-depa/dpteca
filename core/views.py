from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render
from django.views.generic.list import ListView
from django.db.models import Q

from music.models import Artista, Album, Brano

# Create your views here.

""" def homepage(request):
    return render(request, 'core/homepage.html') """
    
"""
    utilizzando queryset anzichè model (di ListView ) sarà possibile utilizzare filtri pittosto che ordinamenti
"""
class HomeView(ListView):
   template_name = "core/homepage.html"
   context_object_name = "lista_artisti"
   
   def get_queryset(self):
       try:
           return Artista.objects.all()
       except Exception as e:
           # Se c'è un errore del database, ritorna una lista vuota
           # Questo permette all'app di partire anche se il database non è pronto
           import logging
           logger = logging.getLogger(__name__)
           logger.error(f"Errore nel caricamento artisti: {e}")
           return Artista.objects.none()

class ArtistaView(ListView):
   queryset = Artista.objects.all().order_by("nome_artista")
   template_name = "core/elenco_artisti.html"
   context_object_name = "lista_artisti"

class AlbumView(ListView):
   queryset = Album.objects.all().order_by("artista_appartenenza", "data_rilascio")
   template_name = "core/elenco_album.html"
   context_object_name = "lista_album"


class UserList(ListView):
    model = User
    template_name = "core/users.html"
    context_object_name = "lista_utenti"


def user_profile_view(request, username):
    user = get_object_or_404(User, username = username)
    context = {"user": user}
    return render(request, "core/user_profile.html", context)


class SearchView(ListView):
    template_name = "core/search_results.html"
    context_object_name = "results"
    
    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            # Search in artists - search in name, profile and members
            artisti = Artista.objects.filter(
                Q(nome_artista__icontains=query) | 
                Q(profilo__icontains=query) |
                Q(componenti__icontains=query)
            ).distinct()
            
            # Search in albums - search in title, artist name, label, genre, and notes
            album = Album.objects.filter(
                Q(titolo_album__icontains=query) | 
                Q(artista_appartenenza__nome_artista__icontains=query) |
                Q(editore__icontains=query) |
                Q(genere__icontains=query) |
                Q(note__icontains=query)
            ).distinct()
            
            # Search in tracks - search in title and credits
            brani = Brano.objects.filter(
                Q(titolo_brano__icontains=query) |
                Q(crediti__icontains=query)
            ).select_related('album_appartenenza', 'album_appartenenza__artista_appartenenza').distinct()
            
            return {
                'artisti': artisti,
                'album': album,
                'brani': brani,
                'query': query
            }
        return {'artisti': [], 'album': [], 'brani': [], 'query': ''}

    

