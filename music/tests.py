from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Artista, Album, Brano
from datetime import date

class ArtistaEditTestCase(TestCase):
    def setUp(self):
        # Create a staff user
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        
        # Create a regular user
        self.regular_user = User.objects.create_user(
            username='regular',
            password='testpass123',
            is_staff=False
        )
        
        # Create a test artist
        self.artista = Artista.objects.create(
            nome_artista='Test Artist',
            profilo='Test profile',
            sites='www.test.com',
            componenti='Test members'
        )
        
        self.client = Client()
    
    def test_edit_artista_staff_access(self):
        """Test that staff users can access the edit page"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('modifica_artista', kwargs={'pk': self.artista.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Modifica Artista')
    
    def test_edit_artista_regular_user_denied(self):
        """Test that regular users cannot access the edit page"""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('modifica_artista', kwargs={'pk': self.artista.pk}))
        self.assertEqual(response.status_code, 403)
    
    def test_edit_artista_anonymous_denied(self):
        """Test that anonymous users cannot access the edit page"""
        response = self.client.get(reverse('modifica_artista', kwargs={'pk': self.artista.pk}))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_edit_artista_form_submission(self):
        """Test that the edit form works correctly"""
        self.client.login(username='staff', password='testpass123')
        
        # Test form submission
        form_data = {
            'nome_artista': 'Updated Artist Name',
            'profilo': 'Updated profile text',
            'sites': 'www.updated.com',
            'componenti': 'Updated members'
        }
        
        response = self.client.post(
            reverse('modifica_artista', kwargs={'pk': self.artista.pk}),
            data=form_data
        )
        
        # Should redirect after successful edit
        self.assertEqual(response.status_code, 302)
        
        # Verify the artist was updated
        updated_artista = Artista.objects.get(pk=self.artista.pk)
        self.assertEqual(updated_artista.nome_artista, 'Updated Artist Name')
        self.assertEqual(updated_artista.profilo, 'Updated profile text')
        self.assertEqual(updated_artista.sites, 'www.updated.com')
        self.assertEqual(updated_artista.componenti, 'Updated members')


class AlbumBraniTestCase(TestCase):
    """Test per verificare che i brani vengano visualizzati correttamente nell'album"""
    
    def setUp(self):
        # Crea un artista
        self.artista = Artista.objects.create(
            nome_artista='Pink Floyd',
            profilo='Progressive rock band'
        )
        
        # Crea un album
        self.album = Album.objects.create(
            titolo_album='The Wall',
            editore='Columbia',
            artista_appartenenza=self.artista,
            data_rilascio=date(1979, 11, 30),
            costo=25.00
        )
        
        # Crea alcuni brani
        self.brano1 = Brano.objects.create(
            titolo_brano='In The Flesh?',
            sezione='a',
            progressivo='1',
            durata='3:19',
            crediti='Waters',
            album_appartenenza=self.album
        )
        
        self.brano2 = Brano.objects.create(
            titolo_brano='The Thin Ice',
            sezione='a',
            progressivo='2',
            durata='2:27',
            crediti='Waters',
            album_appartenenza=self.album
        )
        
        self.brano3 = Brano.objects.create(
            titolo_brano='Another Brick In The Wall Pt.1',
            sezione='a',
            progressivo='3',
            durata='3:21',
            crediti='Waters',
            album_appartenenza=self.album
        )
        
        self.client = Client()
    
    def test_album_view_displays_tracks(self):
        """Test che la vista album mostri tutti i brani"""
        response = self.client.get(reverse('album_view', kwargs={'pk': self.album.pk}))
        
        # Verifica status code
        self.assertEqual(response.status_code, 200)
        
        # Verifica che i brani siano nel context
        self.assertIn('brani_album', response.context)
        brani = response.context['brani_album']
        self.assertEqual(brani.count(), 3)
        
        # Verifica che i titoli dei brani siano nella risposta HTML
        self.assertContains(response, 'In The Flesh?')
        self.assertContains(response, 'The Thin Ice')
        self.assertContains(response, 'Another Brick In The Wall Pt.1')
        
        # Verifica che la tabella dei brani sia presente
        self.assertContains(response, 'table table-striped')
    
    def test_album_tracks_ordering(self):
        """Test che i brani siano ordinati correttamente"""
        response = self.client.get(reverse('album_view', kwargs={'pk': self.album.pk}))
        brani = list(response.context['brani_album'])
        
        # Verifica l'ordine
        self.assertEqual(brani[0].titolo_brano, 'In The Flesh?')
        self.assertEqual(brani[1].titolo_brano, 'The Thin Ice')
        self.assertEqual(brani[2].titolo_brano, 'Another Brick In The Wall Pt.1')
    
    def test_album_tracks_count_badge(self):
        """Test che il badge con il conteggio dei brani sia presente"""
        response = self.client.get(reverse('album_view', kwargs={'pk': self.album.pk}))
        
        # Verifica che il conteggio sia corretto
        self.assertContains(response, '3')  # Numero di brani
        self.assertContains(response, 'badge')
    
    def test_empty_album_shows_message(self):
        """Test che un album senza brani mostri un messaggio appropriato"""
        # Crea un album vuoto
        empty_album = Album.objects.create(
            titolo_album='Empty Album',
            artista_appartenenza=self.artista
        )
        
        response = self.client.get(reverse('album_view', kwargs={'pk': empty_album.pk}))
        
        # Verifica che il messaggio di album vuoto sia presente
        self.assertContains(response, 'Nessun brano disponibile')


class BranoEditDeleteTestCase(TestCase):
    """Test per le funzionalità di modifica ed eliminazione brani"""
    
    def setUp(self):
        # Crea utenti
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            password='testpass123',
            is_staff=False
        )
        
        # Crea dati di test
        self.artista = Artista.objects.create(
            nome_artista='Test Artist'
        )
        
        self.album = Album.objects.create(
            titolo_album='Test Album',
            artista_appartenenza=self.artista
        )
        
        self.brano = Brano.objects.create(
            titolo_brano='Test Track',
            sezione='a',
            progressivo='1',
            durata='3:30',
            crediti='Test Credits',
            album_appartenenza=self.album
        )
        
        self.client = Client()
    
    def test_modifica_brano_staff_access(self):
        """Test che gli utenti staff possano accedere alla pagina di modifica"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('modifica_brano', kwargs={'pk': self.brano.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Modifica Brano')
        self.assertContains(response, 'Test Track')
    
    def test_modifica_brano_regular_user_denied(self):
        """Test che gli utenti normali non possano modificare"""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('modifica_brano', kwargs={'pk': self.brano.pk}))
        self.assertEqual(response.status_code, 403)
    
    def test_modifica_brano_form_submission(self):
        """Test che la modifica del brano funzioni correttamente"""
        self.client.login(username='staff', password='testpass123')
        
        form_data = {
            'titolo_brano': 'Updated Track Title',
            'sezione': 'b',
            'progressivo': '2',
            'durata': '4:00',
            'crediti': 'Updated Credits',
            'album_appartenenza': self.album.pk
        }
        
        response = self.client.post(
            reverse('modifica_brano', kwargs={'pk': self.brano.pk}),
            data=form_data
        )
        
        # Should redirect after successful edit
        self.assertEqual(response.status_code, 302)
        
        # Verify the track was updated
        updated_brano = Brano.objects.get(pk=self.brano.pk)
        self.assertEqual(updated_brano.titolo_brano, 'Updated Track Title')
        self.assertEqual(updated_brano.sezione, 'b')
        self.assertEqual(updated_brano.progressivo, '2')
    
    def test_elimina_brano_staff_access(self):
        """Test che gli utenti staff possano accedere alla pagina di eliminazione"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('elimina_brano', kwargs={'pk': self.brano.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Conferma Eliminazione')
        self.assertContains(response, 'Test Track')
    
    def test_elimina_brano_regular_user_denied(self):
        """Test che gli utenti normali non possano eliminare"""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('elimina_brano', kwargs={'pk': self.brano.pk}))
        self.assertEqual(response.status_code, 403)
    
    def test_elimina_brano_confirmation(self):
        """Test che l'eliminazione del brano funzioni correttamente"""
        self.client.login(username='staff', password='testpass123')
        
        # Verify track exists
        self.assertTrue(Brano.objects.filter(pk=self.brano.pk).exists())
        
        response = self.client.post(
            reverse('elimina_brano', kwargs={'pk': self.brano.pk})
        )
        
        # Should redirect after deletion
        self.assertEqual(response.status_code, 302)
        
        # Verify track was deleted
        self.assertFalse(Brano.objects.filter(pk=self.brano.pk).exists())
    
    def test_brano_buttons_visible_for_staff(self):
        """Test che i pulsanti di modifica/eliminazione siano visibili per staff"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('album_view', kwargs={'pk': self.album.pk}))
        
        # Verifica presenza pulsanti
        self.assertContains(response, 'Modifica')
        self.assertContains(response, 'Elimina')
        self.assertContains(response, reverse('modifica_brano', kwargs={'pk': self.brano.pk}))
        self.assertContains(response, reverse('elimina_brano', kwargs={'pk': self.brano.pk}))
    
    def test_brano_buttons_hidden_for_regular_users(self):
        """Test che i pulsanti non siano visibili per utenti normali"""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('album_view', kwargs={'pk': self.album.pk}))
        
        # I pulsanti non dovrebbero essere presenti
        self.assertNotContains(response, 'btn-outline-primary')
        self.assertNotContains(response, reverse('modifica_brano', kwargs={'pk': self.brano.pk}))
    
    def test_success_messages(self):
        """Test che i messaggi di successo siano mostrati"""
        self.client.login(username='staff', password='testpass123')
        
        # Test messaggio modifica
        form_data = {
            'titolo_brano': 'Updated Track',
            'album_appartenenza': self.album.pk
        }
        
        response = self.client.post(
            reverse('modifica_brano', kwargs={'pk': self.brano.pk}),
            data=form_data,
            follow=True
        )
        
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('modificato con successo', str(messages[0]))
