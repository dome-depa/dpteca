from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.loader import render_to_string
from django.conf import settings
import os
from django.urls import reverse_lazy
from io import BytesIO

from .forms import AlbumModelForm, BranoModelForm, ArtistaModelForm, AlbumDesideratoForm
from django.db.models import Prefetch, Case, When, IntegerField

from .mixins import StaffMixing
from .models import Artista, Album, Brano, AlbumDesiderato
from .services.brani_import import import_tracks_for_album
from .services.musicbrainz import (
    MusicBrainzError,
    get_release_tracks,
    search_releases,
)
from .services.listening import find_bandcamp_url, youtube_search_url

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
        messages.success(self.request, f'Artista "{self.object.nome_artista}" modificato con successo!')
        return self.object.get_absolute_url()

    def form_invalid(self, form):
        messages.error(self.request, 'Errore di validazione: controlla i campi evidenziati e riprova.')
        return super().form_invalid(form)

class ModificaAlbum(StaffMixing, UpdateView):
    model = Album
    form_class = AlbumModelForm
    template_name = "music/modifica_album.html"
    
    def get_success_url(self):
        messages.success(self.request, f'Album "{self.object.titolo_album}" modificato con successo!')
        return self.object.get_absolute_url()
    
    def form_invalid(self, form):
        messages.error(self.request, 'Errore di validazione: controlla i campi evidenziati e riprova.')
        return super().form_invalid(form)

def VisualizzaArtista(request, pk):   
    artista = get_object_or_404(Artista, pk=pk)
    albums_artista = Album.objects.filter(
        artista_appartenenza = artista
        ).annotate(
            classica_in_coda=Case(
                When(genere__iexact="Classica", then=1),
                default=0,
                output_field=IntegerField(),
            )
        ).order_by(
            "classica_in_coda",
            "-genere",
            "artista_appartenenza__nome_artista",
            "supporto",
            "data_rilascio",
            "titolo_album",
        )
    context = {"artista": artista, "discografia": albums_artista}
    return render(request, "music/singolo_artista.html", context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def CreaAlbum(request, pk):
    artista = get_object_or_404(Artista, pk=pk)
    if request.method == "POST":
        form = AlbumModelForm(request.POST, request.FILES)
        if form.is_valid():
            album = form.save(commit=False)
            album.artista_appartenenza = artista
            album.save()
            form.save_m2m()  # Salva relazioni many-to-many (stili)
            messages.success(request, f'Album "{album.titolo_album}" creato con successo!')
            return HttpResponseRedirect(artista.get_absolute_url())
        else:
            messages.error(request, 'Errore di validazione: controlla i campi evidenziati e riprova.')
    else:
        form = AlbumModelForm(initial={'artista_appartenenza': artista})

    context = {"form": form, "artista": artista}
    return render(request, "music/crea_album.html", context)


def VisualizzaAlbum(request, pk):   
    album = get_object_or_404(Album, pk=pk)
    artista = album.artista_appartenenza
    # Usa la relazione inversa per ottenere i brani
    brani_album = album.brani.all().order_by("sezione", "progressivo")
    
    context = {"album": album, "artista": artista, "brani_album": brani_album}
    
    return render(request, "music/singolo_album.html", context)


def ascolta_brano(request, pk):
    brano = get_object_or_404(
        Brano.objects.select_related("album_appartenenza__artista_appartenenza"),
        pk=pk,
    )
    album = brano.album_appartenenza
    artista = album.artista_appartenenza
    artist_name = artista.nome_artista
    album_title = album.titolo_album
    track_title = brano.titolo_brano
    search_query = f"{artist_name} {album_title} {track_title}".strip()

    bandcamp_url = find_bandcamp_url(artist_name, album_title, track_title)
    if bandcamp_url:
        return redirect(bandcamp_url)

    context = {
        "brano": brano,
        "album": album,
        "artista": artista,
        "search_query": search_query,
        "youtube_url": youtube_search_url(artist_name, album_title, track_title),
    }
    return render(request, "music/ascolta_brano.html", context)


def _link_callback(uri, rel):
    """
    Converte URL static/media in percorsi file assoluti per xhtml2pdf.
    """
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith(settings.STATIC_URL):
        static_root = getattr(settings, "STATIC_ROOT", None) or os.path.join(settings.BASE_DIR, "static")
        path = os.path.join(static_root, uri.replace(settings.STATIC_URL, ""))
    else:
        return uri
    return path


def report_artisti_pdf(request):
    """
    Produce un PDF con:
    - Elenco Artisti
    - Per ogni artista: album in ordine di data_rilascio, con copertina, etichetta (editore) e catalogo
    Accesso non ristretto (solo lettura).
    """
    try:
        # Import locale per evitare errori di import a livello modulo in ambienti senza xhtml2pdf
        from xhtml2pdf import pisa
    except ImportError:
        # Fallback: genera PDF con ReportLab
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader
        except ImportError:
            return HttpResponse("PDF non disponibile: installare reportlab.", status=500)

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        x_margin = 14 * mm
        y_margin = 18 * mm
        y = height - y_margin

        c.setFont("Helvetica-Bold", 16)
        c.drawString(x_margin, y, "Elenco Artisti e Discografie")
        y -= 10 * mm

        c.setFont("Helvetica", 10)
        for artista in Artista.objects.all().order_by("nome_artista"):
            # intestazione artista
            if y < 40 * mm:
                c.showPage()
                y = height - y_margin
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x_margin, y, artista.nome_artista or "")
            y -= 6 * mm
            c.setFont("Helvetica", 10)

            # albums: include "Classica" in coda, poi ordina per genere (Z->A), artista, supporto, anno, titolo
            albums_qs = (
                Album.objects.filter(artista_appartenenza=artista)
                .annotate(
                    classica_in_coda=Case(
                        When(genere__iexact="Classica", then=1),
                        default=0,
                        output_field=IntegerField(),
                    )
                )
                .order_by(
                    "classica_in_coda",
                    "-genere",
                    "artista_appartenenza__nome_artista",
                    "supporto",
                    "data_rilascio",
                    "titolo_album",
                )
            )
            for album in albums_qs:
                if y < 30 * mm:
                    c.showPage()
                    y = height - y_margin
                # testo a sinistra
                title = album.titolo_album or ""
                anno = f" ({album.data_rilascio.year})" if album.data_rilascio else ""
                c.drawString(x_margin, y, f"{title}{anno}")
                y -= 5 * mm
                meta_kv = []
                if getattr(album, "genere", None):
                    meta_kv.append(("Genere", album.genere))
                if album.editore:
                    meta_kv.append(("Etichetta", album.editore))
                if album.catalogo:
                    meta_kv.append(("Catalogo", album.catalogo))
                try:
                    num_brani = album.brani.count()
                except Exception:
                    num_brani = 0
                if num_brani:
                    meta_kv.append(("Brani", str(num_brani)))
                if meta_kv:
                    x_text = x_margin
                    for idx, (label_txt, value_txt) in enumerate(meta_kv):
                        # label normale
                        c.setFont("Helvetica", 9)
                        label_render = f"{label_txt}: "
                        c.drawString(x_text, y, label_render)
                        x_text += c.stringWidth(label_render, "Helvetica", 9)
                        # valore corsivo
                        c.setFont("Helvetica-Oblique", 9)
                        c.drawString(x_text, y, str(value_txt))
                        x_text += c.stringWidth(str(value_txt), "Helvetica-Oblique", 9)
                        # separatore per coppie successive
                        if idx < len(meta_kv) - 1:
                            sep = " • "
                            c.setFont("Helvetica", 9)
                            c.drawString(x_text, y, sep)
                            x_text += c.stringWidth(sep, "Helvetica", 9)
                    c.setFont("Helvetica", 10)
                # immagine a destra
                if album.copertina and getattr(album.copertina, "path", None):
                    try:
                        img = ImageReader(album.copertina.path)
                        img_w = img_h = 28 * mm
                        c.drawImage(
                            img,
                            width - x_margin - img_w,
                            y - img_h + 3 * mm,
                            width=img_w,
                            height=img_h,
                            preserveAspectRatio=True,
                            anchor="n",
                        )
                    except Exception:
                        pass
                y -= 10 * mm

            y -= 4 * mm

        # Aggiungi statistiche finali
        if y < 30 * mm:
            c.showPage()
            y = height - y_margin
        
        y -= 10 * mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x_margin, y, "Riepilogo")
        y -= 6 * mm
        c.setFont("Helvetica", 10)
        
        # Conta artisti e album totali (escludendo Classica)
        total_artisti = Artista.objects.count()
        total_albums = Album.objects.exclude(genere__iexact="Classica").count()
        
        c.drawString(x_margin, y, f"Numero totale artisti: {total_artisti}")
        y -= 5 * mm
        c.drawString(x_margin, y, f"Numero totale album: {total_albums}")

        c.showPage()
        c.save()
        pdf = buffer.getvalue()
        buffer.close()
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'inline; filename="artisti_albums.pdf"'
        response.write(pdf)
        return response
    # Include "Classica" in coda, poi ordina per genere (Z->A), artista, supporto, anno, titolo
    albums_ordered = (
        Album.objects.all()
        .annotate(
            classica_in_coda=Case(
                When(genere__iexact="Classica", then=1),
                default=0,
                output_field=IntegerField(),
            )
        )
        .order_by(
            "classica_in_coda",
            "-genere",
            "artista_appartenenza__nome_artista",
            "supporto",
            "data_rilascio",
            "titolo_album",
        )
    )
    artisti = Artista.objects.all().prefetch_related(
        Prefetch("albums", queryset=albums_ordered),
        "albums__stili",
    ).order_by("nome_artista")
    
    # Calcola statistiche totali
    total_artisti = Artista.objects.count()
    total_albums = Album.objects.exclude(genere__iexact="Classica").count()
    
    # ordina gli album per data_rilascio discendente a livello di template
    html = render_to_string(
        "music/report_artisti_albums.html",
        {
            "artisti": artisti,
            "MEDIA_URL": settings.MEDIA_URL,
            "total_artisti": total_artisti,
            "total_albums": total_albums,
        },
    )
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="artisti_albums.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=_link_callback, encoding="utf-8")
    if pisa_status.err:
        return HttpResponse("Errore nella generazione del PDF", status=500)
    return response

@login_required
@user_passes_test(lambda u: u.is_staff)
def importa_brani_album(request, pk):
    album = get_object_or_404(Album, pk=pk)
    artista = album.artista_appartenenza
    release_mbid = request.GET.get("release_mbid") or request.POST.get("release_mbid")
    release_date = album.data_rilascio.isoformat() if album.data_rilascio else None

    if request.method == "POST" and release_mbid:
        skip_existing = request.POST.get("skip_existing") == "on"
        update_existing = request.POST.get("update_existing") == "on"
        try:
            tracks = get_release_tracks(release_mbid)
        except MusicBrainzError as exc:
            messages.error(request, str(exc))
            return redirect("importa_brani_album", pk=album.pk)

        if not tracks:
            messages.warning(request, "Nessun brano trovato per la release selezionata.")
            return redirect("importa_brani_album", pk=album.pk)

        result = import_tracks_for_album(
            album,
            tracks,
            skip_existing=skip_existing,
            update_existing=update_existing,
        )
        messages.success(
            request,
            f"Import completato: {result.created} creati, "
            f"{result.updated} aggiornati, {result.skipped} saltati.",
        )
        return redirect("album_view", pk=album.pk)

    releases = []
    tracks = []
    selected_release = None
    api_error = None

    try:
        releases = search_releases(
            artista.nome_artista,
            album.titolo_album,
            release_date,
        )
        if release_mbid:
            tracks = get_release_tracks(release_mbid)
            selected_release = next(
                (candidate for candidate in releases if candidate.mbid == release_mbid),
                None,
            )
    except MusicBrainzError as exc:
        api_error = str(exc)

    existing_titles = {
        title.lower()
        for title in album.brani.values_list("titolo_brano", flat=True)
    }

    context = {
        "album": album,
        "artista": artista,
        "releases": releases,
        "tracks": tracks,
        "selected_release": selected_release,
        "release_mbid": release_mbid,
        "api_error": api_error,
        "existing_titles": existing_titles,
        "existing_count": album.brani.count(),
    }
    return render(request, "music/importa_brani_album.html", context)


@login_required
@user_passes_test(lambda u: u.is_staff)
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
        form = BranoModelForm(initial={'album_appartenenza': album})

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


class EliminaAlbum(StaffMixing, DeleteView):
    model = Album
    template_name = "music/elimina_album.html"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        album = self.object
        artista = album.artista_appartenenza
        num_brani = album.brani.count()
        response = super().delete(request, *args, **kwargs)
        if num_brani:
            messages.success(request, f'Album "{album.titolo_album}" e {num_brani} brani associati eliminati con successo!')
        else:
            messages.success(request, f'Album "{album.titolo_album}" eliminato con successo!')
        return response

    def get_success_url(self):
        # Dopo l'eliminazione dell'album, torna alla pagina dell'artista
        return self.object.artista_appartenenza.get_absolute_url()


class ListaAlbumDesiderati(ListView):
    model = AlbumDesiderato
    template_name = "music/album_desiderati.html"
    context_object_name = "album_desiderati"

    def get_queryset(self):
        return (
            AlbumDesiderato.objects.select_related("artista")
            .order_by("artista__nome_artista", "titolo_album", "copertina")
        )


class CreaAlbumDesiderato(StaffMixing, CreateView):
    model = AlbumDesiderato
    form_class = AlbumDesideratoForm
    template_name = "music/crea_album_desiderato.html"

    def get_initial(self):
        initial = super().get_initial()
        artista_id = self.request.GET.get("artista")
        titolo = self.request.GET.get("titolo")
        if artista_id:
            initial["artista"] = artista_id
        if titolo:
            initial["titolo_album"] = titolo
        return initial

    def get_success_url(self):
        return reverse("album_desiderati")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["artisti"] = Artista.objects.all().order_by("nome_artista")
        return context


class ModificaAlbumDesiderato(StaffMixing, UpdateView):
    model = AlbumDesiderato
    form_class = AlbumDesideratoForm
    template_name = "music/modifica_album_desiderato.html"

    def get_success_url(self):
        return reverse("album_desiderati")


class EliminaAlbumDesiderato(StaffMixing, DeleteView):
    model = AlbumDesiderato
    template_name = "music/elimina_album_desiderato.html"

    def get_success_url(self):
        return reverse("album_desiderati")
