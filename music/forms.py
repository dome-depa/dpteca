from django import forms

from .models import Album, Brano, Artista, AlbumDesiderato

class AlbumModelForm(forms.ModelForm):

    class Meta:
        model = Album
        fields = "__all__"
        widgets = {
            'artista_appartenenza': forms.HiddenInput(),
        }
       
class BranoModelForm(forms.ModelForm):

    class Meta:
        model = Brano
        fields = "__all__"
        widgets = {
            'album_appartenenza': forms.HiddenInput(),
        }

class ArtistaModelForm(forms.ModelForm):
    
    class Meta:
        model = Artista
        fields = "__all__"
        widgets = {
            'profilo': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }


class AlbumDesideratoForm(forms.ModelForm):
    artista_nome = forms.CharField(
        label="Artista",
        help_text="Digita parte del nome e seleziona l'artista corretto.",
        widget=forms.TextInput(attrs={"list": "artisti-list"}),
    )

    class Meta:
        model = AlbumDesiderato
        fields = ["artista", "titolo_album", "copertina"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "artista" in self.fields:
            self.fields["artista"].queryset = Artista.objects.all().order_by("nome_artista")
            self.fields["artista"].widget = forms.HiddenInput()

    def clean_artista_nome(self):
        nome = (self.cleaned_data.get("artista_nome") or "").strip()
        if not nome:
            raise forms.ValidationError("Seleziona un artista.")
        qs = Artista.objects.filter(nome_artista__icontains=nome).order_by("nome_artista")
        if qs.count() == 1:
            self.cleaned_data["artista"] = qs.first()
            return nome
        if qs.count() == 0:
            raise forms.ValidationError("Nessun artista trovato. Affina la ricerca.")
        raise forms.ValidationError("Più artisti trovati. Specifica meglio il nome.")