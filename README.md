# dPteca - Sistema di Gestione Discoteca Digitale

Sistema di gestione per collezioni musicali sviluppato con Django 5.2.7.

## 📋 Caratteristiche Principali

### Gestione Artisti
- Lista completa degli artisti
- Pagina dettaglio artista con foto, profilo e componenti
- Visualizzazione discografia completa
- Modifica e creazione artisti (solo staff)

### Gestione Album
- Lista album con copertine
- Dettagli completi album (etichetta, catalogo, genere, stili, supporto, data rilascio)
- Visualizzazione lista brani per ogni album
- Badge conteggio brani
- Stato completamento album
- Modifica e creazione album (solo staff)

### Gestione Brani
- Lista brani organizzata per album
- Tabella con: numero progressivo, sezione (lato A/B), titolo, crediti, durata
- Ordinamento automatico per sezione e progressivo
- Creazione brani (solo staff)

### Funzionalità Aggiuntive
- 🔍 **Ricerca**: cerca artisti e album
- 🍞 **Breadcrumb navigation**: navigazione gerarchica completa
- 👤 **Autenticazione utenti**: registrazione, login, logout
- 🔐 **Permessi staff**: gestione contenuti riservata
- 📱 **Responsive design**: Bootstrap 5
- ✅ **Test suite completa**: test per tutte le funzionalità principali

## 🗂️ Struttura del Progetto

```
mysite/
├── accounts/           # App gestione utenti
├── core/              # App principale (homepage, liste, ricerca)
├── music/             # App gestione musicale (artisti, album, brani)
├── templates/         # Template globali
├── static-storage/    # File statici CSS
└── mysite/           # Configurazione Django
```

## 🎵 Modelli Database

### Artista
- Nome artista
- Foto
- Profilo/biografia
- Componenti del gruppo
- Siti web

### Album
- Titolo
- Artista di appartenenza
- Editore/Etichetta
- Numero di catalogo
- Genere
- Stili (ManyToMany)
- Supporto (CD, Vinile, ecc.)
- Data di rilascio
- Deposito/Ubicazione
- Copertina
- Costo
- Stato completamento

### Brano
- Titolo
- Album di appartenenza
- Sezione (lato A/B, CD1/CD2, ecc.)
- Numero progressivo
- Crediti (autori/compositori)
- Durata

### Stile
- Nome stile musicale

## 🚀 Installazione e Avvio

### Prerequisiti
- Python 3.12+
- pip

### Setup

1. **Clona il repository**
```bash
git clone <repository-url>
cd mysite
```

2. **Crea e attiva l'ambiente virtuale**
```bash
python3 -m venv my-env
source my-env/bin/activate  # Su Windows: my-env\Scripts\activate
```

3. **Installa le dipendenze**
```bash
pip install django==5.2.7
pip install django-crispy-forms
pip install crispy-bootstrap5
pip install pillow  # Per la gestione delle immagini
```

4. **Esegui le migrazioni**
```bash
python manage.py migrate
```

5. **Crea un superuser**
```bash
python manage.py createsuperuser
```

6. **Avvia il server**
```bash
python manage.py runserver
```

7. **Apri il browser**
```
http://127.0.0.1:8000/
```

## 🧪 Test

Esegui i test con:
```bash
python manage.py test
```

Test specifici per album e brani:
```bash
python manage.py test music.tests.AlbumBraniTestCase -v 2
```

## 📱 URL Principali

- `/` - Homepage
- `/lista-artisti` - Lista artisti
- `/lista-album` - Lista album
- `/music/artista/<id>/` - Dettaglio artista
- `/music/album/<id>/` - Dettaglio album con lista brani
- `/music/nuovo-artista/` - Crea artista (staff)
- `/music/artista/<id>/crea-album/` - Crea album (staff)
- `/music/album/<id>/crea-brano/` - Crea brano (staff)
- `/search/` - Ricerca
- `/accounts/registrazione/` - Registrazione utente
- `/accounts/login/` - Login

## 👥 Permessi

### Utenti Normali
- Visualizzazione artisti, album e brani
- Ricerca
- Visualizzazione profilo utente

### Staff
- Tutte le funzionalità degli utenti normali
- Creazione artisti
- Creazione album
- Creazione brani
- Modifica artisti
- Modifica album

## 🎨 Tecnologie Utilizzate

- **Backend**: Django 5.2.7
- **Frontend**: Bootstrap 5.2.3
- **Forms**: Django Crispy Forms + Crispy Bootstrap 5
- **Database**: SQLite (development)
- **Template Engine**: Django Templates
- **CSS Custom**: dPteca.css

## 📝 Note di Sviluppo

### Navigazione Breadcrumb
Struttura gerarchica implementata:
```
Home → Lista Artisti → Artista → Album → Brani
```

### Ordinamento Brani
I brani sono ordinati automaticamente per:
1. Sezione (a, b, c, ...)
2. Progressivo (1, 2, 3, ...)

### Success URLs
Dopo creazione/modifica, l'utente viene reindirizzato alla pagina dell'oggetto:
- Crea artista → Pagina artista
- Modifica artista → Pagina artista
- Modifica album → Pagina album
- Crea brano → Pagina album

## 🐛 Troubleshooting

### Porta già in uso
```bash
lsof -ti:8000 | xargs kill -9
python manage.py runserver
```

### Immagini non visualizzate
Verifica che `MEDIA_ROOT` e `MEDIA_URL` siano configurati in `settings.py`

### Migrazioni
Se hai problemi con le migrazioni:
```bash
python manage.py makemigrations
python manage.py migrate
```

## 📄 Licenza

Progetto personale per gestione collezione musicale.

## 👨‍💻 Autore

Domenico De Pace - dPteca Project

---

**Versione**: 1.0.0
**Data**: Ottobre 2025
**Django Version**: 5.2.7

