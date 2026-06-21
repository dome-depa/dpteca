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
- **Creazione brani** (solo staff)
- **Modifica brani** (solo staff) - form completo
- **Eliminazione brani** (solo staff) - con pagina di conferma
- Pulsanti azione inline nella tabella (Modifica/Elimina)
- Messaggi di successo dopo operazioni

### Funzionalità Aggiuntive
- 🔍 **Ricerca avanzata**: cerca artisti, album e brani in 10 campi
- 🍞 **Breadcrumb navigation**: navigazione gerarchica completa
- 👤 **Autenticazione utenti**: registrazione, login, logout
- 🔐 **Permessi staff**: gestione contenuti riservata
- 💬 **Sistema messaggi**: feedback immediato per ogni operazione
- 📱 **Responsive design**: Bootstrap 5
- ✅ **Test suite completa**: 33 test per tutte le funzionalità
- 🗑️ **Conferme eliminazione**: pagine dedicate per operazioni critiche

## 🗂️ Struttura del Progetto

```
dpteca/
├── accounts/           # App gestione utenti
├── core/              # App principale (homepage, liste, ricerca)
├── music/             # App gestione musicale (artisti, album, brani)
├── templates/         # Template globali
├── static-storage/    # File statici CSS
└── dpteca/           # Configurazione Django
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
cd dpteca
```

2. **Crea e attiva l'ambiente virtuale**
```bash
python3 -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate
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

### Visualizzazione
- `/` - Homepage
- `/lista-artisti` - Lista artisti
- `/lista-album` - Lista album
- `/music/artista/<id>/` - Dettaglio artista
- `/music/album/<id>/` - Dettaglio album con lista brani
- `/search/` - Ricerca (artisti, album, brani)

### Gestione (Staff Only)
- `/music/nuovo-artista/` - Crea artista
- `/music/artista/<id>/modifica/` - Modifica artista
- `/music/artista/<id>/crea-album/` - Crea album
- `/music/album/<id>/modifica/` - Modifica album
- `/music/album/<id>/crea-brano/` - Crea brano
- `/music/brano/<id>/modifica/` - Modifica brano
- `/music/brano/<id>/elimina/` - Elimina brano

### Autenticazione
- `/accounts/registrazione/` - Registrazione utente
- `/accounts/login/` - Login
- `/accounts/logout/` - Logout
- `/accounts/password_change/` - Cambio password

## 👥 Permessi

### Utenti Normali
- Visualizzazione artisti, album e brani
- Ricerca
- Visualizzazione profilo utente

### Staff
- Tutte le funzionalità degli utenti normali
- **CRUD Completo Artisti**: Crea, Modifica, Visualizza
- **CRUD Completo Album**: Crea, Modifica, Visualizza
- **CRUD Completo Brani**: Crea, Modifica, Elimina, Visualizza
- Accesso a tutte le pagine di gestione
- Pulsanti azione visibili nelle tabelle

## 🎨 Tecnologie Utilizzate

- **Backend**: Django 5.2.7
- **Frontend**: Bootstrap 5.2.3
- **Forms**: Django Crispy Forms + Crispy Bootstrap 5
- **Database**: PostgreSQL (required)
- **Template Engine**: Django Templates
- **CSS Custom**: dPteca.css
- **Testing**: Django TestCase (33 test passing)
- **Messages**: Django Messages Framework

## 📝 Note di Sviluppo

### Navigazione Breadcrumb
Struttura gerarchica implementata:
```
Home → Lista Artisti → Artista → Album → Azioni Brani
```

### Ordinamento Brani
I brani sono ordinati automaticamente per:
1. Sezione (a, b, c, ...)
2. Progressivo (1, 2, 3, ...)

### Success URLs e Messaggi
Dopo ogni operazione, l'utente viene reindirizzato e riceve un messaggio:
- **Crea artista** → Pagina artista + messaggio successo
- **Modifica artista** → Pagina artista + messaggio successo
- **Modifica album** → Pagina album + messaggio successo
- **Crea brano** → Pagina album + "Brano aggiunto con successo!"
- **Modifica brano** → Pagina album + "Brano modificato con successo!"
- **Elimina brano** → Pagina album + "Brano eliminato con successo!"

### Sicurezza
- **StaffMixing**: Tutte le operazioni di modifica/eliminazione richiedono permessi staff
- **Template Protection**: I pulsanti sono nascosti agli utenti normali
- **URL Protection**: Accesso diretto agli URL protetti restituisce 403 Forbidden
- **Conferme Eliminazione**: Pagina dedicata per confermare operazioni irreversibili

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

Domenico de Paoli - dPteca Project

---

## 📊 Statistiche Progetto

- **Commit Git**: 4
- **File Tracciati**: 66
- **Test**: 33 (tutti passing)
- **Modelli**: 4 (Artista, Album, Brano, Stile)
- **View**: 15+
- **Template**: 26+
- **Campi Ricercabili**: 10
- **Linee di Codice**: ~2000+

## 🎯 Funzionalità Complete

✅ **CRUD Artisti**: Create, Read, Update  
✅ **CRUD Album**: Create, Read, Update  
✅ **CRUD Brani**: Create, Read, Update, Delete  
✅ **Ricerca Multi-Modello**: Artisti, Album, Brani  
✅ **Autenticazione**: Registrazione, Login, Logout  
✅ **Permessi**: Staff/Regular User  
✅ **UI/UX**: Responsive, Messaggi, Breadcrumb  
✅ **Test**: Coverage completo  

---

**Versione**: 2.0.0
**Data**: Ottobre 2025
**Django Version**: 5.2.7
**Ultima Feature**: CRUD Completo Brani con Edit/Delete

