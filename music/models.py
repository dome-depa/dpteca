from django.db import models
from django.urls import reverse
# Create your models here.

""" il modello generico di un Autore """
class Artista(models.Model):
    nome_artista = models.CharField(max_length=120)  
    foto_artista = models.ImageField(blank=True, null=True)
    profilo = models.TextField(blank=True, null=True)
    sites = models.CharField(max_length=100, blank=True, null=True)
    componenti = models.CharField(max_length=300, blank=True, null=True, default=None)
   
    def __str__(self):
        return self.nome_artista

    def get_albums_number(self):
        return Album.objects.filter(artista_appartenenza=self).count()

    def get_albums_closed(self):
        return Album.objects.filter(artista_appartenenza=self, closed=True).count()
    
    def get_absolute_url(self):
        return reverse("artista_view", kwargs={"pk": self.pk})

    class Meta:
        verbose_name = "Artista"
        verbose_name_plural = "Artisti"

class Stile(models.Model):
    stile = models.CharField(max_length=20)

    def __str__(self):
        return str(self.stile)

    class Meta:
        verbose_name = "Stile"
        verbose_name_plural = "Stili"


class Album(models.Model):
    titolo_album = models.CharField(max_length=140)
    editore = models.CharField(max_length=40, blank=True, null=True)
    catalogo = models.CharField(max_length=30, blank=True, null=True)
    genere = models.CharField(max_length=30, blank=True, null=True)  
    stili = models.ManyToManyField(Stile, blank=True)  
    supporto = models.CharField(max_length=20, blank=True, null=True)
    data_rilascio = models.DateField(blank=True, null=True)
    deposito = models.CharField(max_length=10, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    copertina = models.ImageField(blank=True, null=True)
    artista_appartenenza = models.ForeignKey(Artista, on_delete=models.CASCADE, related_name="albums")
    costo = models.FloatField(help_text="in EU €", default=0)
    closed = models.BooleanField(default=False)
    
    def __str__(self):
        return self.titolo_album

    def get_stili(self):
        return self.stili.all()

    def get_absolute_url(self):
        return reverse("album_view", kwargs={"pk": self.pk})        

    class Meta:
        verbose_name = "Album"
        verbose_name_plural = "Albums"


class Brano(models.Model):
    titolo_brano = models.CharField(max_length=150)
    sezione = models.CharField(max_length=2, blank=True, null=True)
    progressivo = models.CharField(max_length=3, blank=True, null=True)    
    crediti = models.CharField(max_length=100, blank=True, null=True)
    durata = models.CharField(max_length=5, blank=True, null=True)
    album_appartenenza = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="brani")

    def __str__(self):
        return self.titolo_brano

    def get_absolute_url(self):
        return reverse("album_view", kwargs={"pk": self.album_appartenenza.pk})       

    class Meta:
        verbose_name = "Brano"
        verbose_name_plural = "Brani"




