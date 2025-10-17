from django.urls import path
from . import views

urlpatterns = [
    path('nuovo-artista/', views.CreaArtista.as_view(), name="crea_artista"),
    path('artista/<int:pk>/', views.VisualizzaArtista, name="artista_view"),
    path('artista/<int:pk>/modifica/', views.ModificaArtista.as_view(), name="modifica_artista"),
    path('artista/<int:pk>/crea-album/', views.CreaAlbum, name="crea_album"),
    path('album/<int:pk>/', views.VisualizzaAlbum, name="album_view"),
    path('album/<int:pk>/modifica/', views.ModificaAlbum.as_view(), name="modifica_album"),
    path('album/<int:pk>/crea-brano/', views.crea_brano, name="crea_brano"),

]