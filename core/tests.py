from django.test import TestCase, Client
from django.urls import reverse
from music.models import Artista, Album, Brano
from datetime import date


class SearchFunctionalityTestCase(TestCase):
    """Test per la funzionalità di ricerca"""
    
    def setUp(self):
        # Crea artisti
        self.pink_floyd = Artista.objects.create(
            nome_artista='Pink Floyd',
            profilo='Progressive rock band from England',
            componenti='Roger Waters, David Gilmour, Nick Mason, Richard Wright'
        )
        
        self.beatles = Artista.objects.create(
            nome_artista='The Beatles',
            profilo='Rock band from Liverpool',
            componenti='John Lennon, Paul McCartney, George Harrison, Ringo Starr'
        )
        
        # Crea album
        self.dark_side = Album.objects.create(
            titolo_album='The Dark Side Of The Moon',
            editore='Harvest',
            genere='Prog Rock',
            artista_appartenenza=self.pink_floyd,
            data_rilascio=date(1973, 3, 1),
            note='One of the best-selling albums of all time'
        )
        
        self.abbey_road = Album.objects.create(
            titolo_album='Abbey Road',
            editore='Apple',
            genere='Rock',
            artista_appartenenza=self.beatles,
            data_rilascio=date(1969, 9, 26)
        )
        
        # Crea brani
        self.brano1 = Brano.objects.create(
            titolo_brano='Money',
            sezione='b',
            progressivo='6',
            durata='6:23',
            crediti='Waters',
            album_appartenenza=self.dark_side
        )
        
        self.brano2 = Brano.objects.create(
            titolo_brano='Come Together',
            sezione='a',
            progressivo='1',
            durata='4:20',
            crediti='Lennon-McCartney',
            album_appartenenza=self.abbey_road
        )
        
        self.brano3 = Brano.objects.create(
            titolo_brano='Time',
            sezione='a',
            progressivo='4',
            durata='6:53',
            crediti='Mason, Waters, Wright, Gilmour',
            album_appartenenza=self.dark_side
        )
        
        self.client = Client()
    
    def test_search_artist_by_name(self):
        """Test ricerca artista per nome"""
        response = self.client.get(reverse('search'), {'q': 'Pink Floyd'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(response.context['results']['artisti'].count(), 1)
        self.assertEqual(response.context['results']['artisti'][0].nome_artista, 'Pink Floyd')
    
    def test_search_artist_by_profile(self):
        """Test ricerca artista per profilo"""
        response = self.client.get(reverse('search'), {'q': 'Liverpool'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['results']['artisti'].count(), 1)
        self.assertEqual(response.context['results']['artisti'][0].nome_artista, 'The Beatles')
    
    def test_search_artist_by_members(self):
        """Test ricerca artista per componenti"""
        response = self.client.get(reverse('search'), {'q': 'Gilmour'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['results']['artisti'].count(), 1)
        self.assertEqual(response.context['results']['artisti'][0].nome_artista, 'Pink Floyd')
    
    def test_search_album_by_title(self):
        """Test ricerca album per titolo"""
        response = self.client.get(reverse('search'), {'q': 'Abbey Road'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['results']['album'].count(), 1)
        self.assertEqual(response.context['results']['album'][0].titolo_album, 'Abbey Road')
    
    def test_search_album_by_artist_name(self):
        """Test ricerca album per nome artista"""
        response = self.client.get(reverse('search'), {'q': 'Beatles'})
        self.assertEqual(response.status_code, 200)
        # Trova sia l'artista che l'album
        self.assertGreaterEqual(response.context['results']['album'].count(), 1)
        self.assertIn('Abbey Road', [a.titolo_album for a in response.context['results']['album']])
    
    def test_search_album_by_label(self):
        """Test ricerca album per etichetta"""
        response = self.client.get(reverse('search'), {'q': 'Harvest'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['results']['album'].count(), 1)
        self.assertEqual(response.context['results']['album'][0].titolo_album, 'The Dark Side Of The Moon')
    
    def test_search_album_by_genre(self):
        """Test ricerca album per genere"""
        response = self.client.get(reverse('search'), {'q': 'Prog'})
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.context['results']['album'].count(), 1)
    
    def test_search_track_by_title(self):
        """Test ricerca brano per titolo"""
        response = self.client.get(reverse('search'), {'q': 'Money'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['results']['brani'].count(), 1)
        self.assertEqual(response.context['results']['brani'][0].titolo_brano, 'Money')
    
    def test_search_track_by_credits(self):
        """Test ricerca brano per crediti"""
        response = self.client.get(reverse('search'), {'q': 'Lennon-McCartney'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['results']['brani'].count(), 1)
        self.assertEqual(response.context['results']['brani'][0].titolo_brano, 'Come Together')
    
    def test_search_multiple_results(self):
        """Test ricerca che trova risultati multipli"""
        response = self.client.get(reverse('search'), {'q': 'Waters'})
        self.assertEqual(response.status_code, 200)
        # Trova l'artista (nei componenti) e i brani (nei crediti)
        self.assertGreaterEqual(response.context['results']['artisti'].count(), 1)
        self.assertGreaterEqual(response.context['results']['brani'].count(), 1)
    
    def test_search_case_insensitive(self):
        """Test che la ricerca sia case-insensitive"""
        response1 = self.client.get(reverse('search'), {'q': 'pink floyd'})
        response2 = self.client.get(reverse('search'), {'q': 'PINK FLOYD'})
        response3 = self.client.get(reverse('search'), {'q': 'Pink Floyd'})
        
        self.assertEqual(response1.context['results']['artisti'].count(), 
                        response2.context['results']['artisti'].count())
        self.assertEqual(response2.context['results']['artisti'].count(), 
                        response3.context['results']['artisti'].count())
    
    def test_search_no_results(self):
        """Test ricerca senza risultati"""
        response = self.client.get(reverse('search'), {'q': 'xyz123notfound'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['results']['artisti'].count(), 0)
        self.assertEqual(response.context['results']['album'].count(), 0)
        self.assertEqual(response.context['results']['brani'].count(), 0)
        self.assertContains(response, 'Nessun risultato trovato')
    
    def test_search_empty_query(self):
        """Test ricerca con query vuota"""
        response = self.client.get(reverse('search'), {'q': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']['artisti']), 0)
        self.assertEqual(len(response.context['results']['album']), 0)
    
    def test_search_partial_match(self):
        """Test ricerca con corrispondenza parziale"""
        response = self.client.get(reverse('search'), {'q': 'Pink'})
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.context['results']['artisti'].count(), 1)
        self.assertEqual(response.context['results']['artisti'][0].nome_artista, 'Pink Floyd')
    
    def test_search_results_display(self):
        """Test che i risultati siano visualizzati correttamente"""
        response = self.client.get(reverse('search'), {'q': 'Pink Floyd'})
        self.assertContains(response, 'Pink Floyd')
        self.assertContains(response, 'Artisti')
    
    def test_search_track_shows_album_link(self):
        """Test che i risultati dei brani includano il link all'album"""
        response = self.client.get(reverse('search'), {'q': 'Money'})
        self.assertEqual(response.status_code, 200)
        # Verifica che ci sia un link all'album
        self.assertContains(response, 'The Dark Side Of The Moon')
        self.assertContains(response, 'Vai all\'Album')
