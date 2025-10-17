from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages

from .forms import AlbumModelForm, BranoModelForm, ArtistaModelForm

from .mixins import StaffMixing
from .models import Artista, Album, Brano

# Create your views here.

class CreaArtista(StaffMixing, CreateView):
    model =  Artista
    form_class = ArtistaModelForm
    template_name = "music/crea_artista.html"
    
    def get_success_url(self):
        return self.object.get_absolute_url()

class ModificaArtista(StaffMixing, UpdateView):
    model = Artista
    form_class = ArtistaModelForm
    template_name = "music/modifica_artista.html"
    
    def get_success_url(self):
        return self.object.get_absolute_url()

class ModificaAlbum(StaffMixing, UpdateView):
    model = Album
    form_class = AlbumModelForm
    template_name = "music/modifica_album.html"
    
    def get_success_url(self):
        return self.object.get_absolute_url()

def VisualizzaArtista(request, pk):   
    artista = get_object_or_404(Artista, pk=pk)
    albums_artista = Album.objects.filter(
        artista_appartenenza = artista
        ).order_by("-data_rilascio")
    context = {"artista": artista, "discografia": albums_artista}
    return render(request, "music/singolo_artista.html", context)


def CreaAlbum(request, pk):
    artista = get_object_or_404(Artista, pk=pk)
    if request.method == "POST":
        form = AlbumModelForm(request.POST)
        if form.is_valid():
            album = form.save(commit=False)
            album.artista_appartenenza = artista
            album.save()
           
            return HttpResponseRedirect(artista.get_absolute_url())
    else:
        form = AlbumModelForm()

    context = {"form": form, "artista": artista}
    return render(request, "music/crea_album.html", context)


def VisualizzaAlbum(request, pk):   
    album = get_object_or_404(Album, pk=pk)
    artista = album.artista_appartenenza
    # Usa la relazione inversa per ottenere i brani
    brani_album = album.brani.all().order_by("sezione", "progressivo")
    
    context = {"album": album, "artista": artista, "brani_album": brani_album}
    
    return render(request, "music/singolo_album.html", context)


def crea_brano(request, pk):
    album = get_object_or_404(Album, pk=pk)
    if request.method == "POST":
        form = BranoModelForm(request.POST)
        if form.is_valid():
            brano = form.save(commit=False)
            brano.album_appartenenza = album
            brano.save()
            messages.success(request, f'Brano "{brano.titolo_brano}" aggiunto con successo!')
            return HttpResponseRedirect(album.get_absolute_url())
    else:
        form = BranoModelForm()

    context = {"form": form, "album": album}
    return render(request, "music/crea_brano.html", context)


class ModificaBrano(StaffMixing, UpdateView):
    model = Brano
    form_class = BranoModelForm
    template_name = "music/modifica_brano.html"
    
    def get_success_url(self):
        messages.success(self.request, f'Brano "{self.object.titolo_brano}" modificato con successo!')
        return self.object.album_appartenenza.get_absolute_url()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['album'] = self.object.album_appartenenza
        return context


class EliminaBrano(StaffMixing, DeleteView):
    model = Brano
    template_name = "music/elimina_brano.html"
    
    def get_success_url(self):
        messages.success(self.request, f'Brano "{self.object.titolo_brano}" eliminato con successo!')
        return self.object.album_appartenenza.get_absolute_url()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['album'] = self.object.album_appartenenza
        return context
