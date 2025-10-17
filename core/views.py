from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render
from django.views.generic.list import ListView
from django.db.models import Q

from music.models import Artista, Album

# Create your views here.

""" def homepage(request):
    return render(request, 'core/homepage.html') """
    
"""
    utilizzando queryset anzichè model (di ListView ) sarà possibile utilizzare filtri pittosto che ordinamenti
"""
class HomeView(ListView):
   queryset = Artista.objects.all()
   template_name = "core/homepage.html"
   context_object_name = "lista_artisti"

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
            # Search in artists and albums
            artisti = Artista.objects.filter(
                Q(nome_artista__icontains=query) | 
                Q(genere__icontains=query)
            )
            album = Album.objects.filter(
                Q(titolo_album__icontains=query) | 
                Q(artista_appartenenza__nome_artista__icontains=query)
            )
            return {
                'artisti': artisti,
                'album': album,
                'query': query
            }
        return {'artisti': [], 'album': [], 'query': ''}

    

