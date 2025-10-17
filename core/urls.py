from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name="homepage"),
    path('lista-artisti', views.ArtistaView.as_view(), name="artista_list"),
    path('lista-album', views.AlbumView.as_view(), name="album_list"),
    path('users/', views.UserList.as_view(), name="user_list"),
    path('user/<str:username>/', views.user_profile_view, name="user_profile"),
    path('search/', views.SearchView.as_view(), name="search"),
]
