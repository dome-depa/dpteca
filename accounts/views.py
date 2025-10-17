from django.shortcuts import render, HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from accounts.forms import FormRegistrazione

# Create your views here.

# creiamo la funzione di registraione
# come prima cosa verifichiamo se il metodo della richiesta è di tipo POST
def registrazione_view(request): 
    if request.method == "POST":
        form = FormRegistrazione(request.POST)
        if form.is_valid():                      #prendiamo i dati dicui abbiamo bisogno
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password1"]
            User.objects.create_user(                  # creiamo l'oggetto user
                username=username,
                password=password,
                email=email
            )                                        
            user = authenticate(username=username, password=password)      # autentichiamo lo user 
            login(request, user)
            return HttpResponseRedirect("/")                # andiamo a reindirizzarlo sulla home page
    else:
        form = FormRegistrazione()
    
    context = {"form": form}
    return render(request, "accounts/registrazione.html", context)     #accetta una richiesta e il template che isogna creare.
#
# 
# ora rimane da ceare il template e la mappatura degli url

