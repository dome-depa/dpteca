from django.contrib import admin

# Register your models here.
from .models import Artista, Album, Brano, Stile

# Register your models here.

class AlbumModelAdmin(admin.ModelAdmin):
    model = Album
    list_display = ["titolo_album", "artista_appartenenza", "editore", "catalogo", "closed"]
    search_fields = ["titolo_album", "artista_appartenenza"]
    list_filter = ["titolo_album", "artista_appartenenza" ]
    
class BranoModelAdmin(admin.ModelAdmin):
    model = Brano
    list_display = ["titolo_brano", "album_appartenenza", "sezione", "progressivo", "durata"]
    search_fields = ["titolo_brano", "album_appartenenza"]
    list_filter = ["titolo_brano", "album_appartenenza"]

class ArtistaModelAdmin(admin.ModelAdmin):
    model = Artista
    list_display = ["nome_artista", "componenti", "sites"]
    
   
admin.site.register(Stile)
admin.site.register(Artista, ArtistaModelAdmin)
admin.site.register(Album, AlbumModelAdmin)
admin.site.register(Brano, BranoModelAdmin)