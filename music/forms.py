from django import forms

from .models import Album, Brano, Artista

class AlbumModelForm(forms.ModelForm):

    class Meta:
        model = Album
        fields = "__all__"
       
class BranoModelForm(forms.ModelForm):

    class Meta:
        model = Brano
        fields = "__all__"

class ArtistaModelForm(forms.ModelForm):
    
    class Meta:
        model = Artista
        fields = "__all__"
        widgets = {
            'profilo': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }