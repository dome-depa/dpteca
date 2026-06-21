from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from music.models import Album, Artista, Brano
from music.services.listening import (
    find_bandcamp_url,
    find_listen_url,
    youtube_search_url,
)


class ListeningServiceTestCase(TestCase):
    @patch("music.services.listening.requests.get")
    def test_find_bandcamp_url_from_autocomplete(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {
            "results": [
                {
                    "itemtype": "t",
                    "url": "https://artist.bandcamp.com/track/demo",
                }
            ]
        }

        url = find_bandcamp_url("Artist", "Album", "Track")

        self.assertEqual(url, "https://artist.bandcamp.com/track/demo")

    def test_youtube_search_url(self):
        url = youtube_search_url("Pink Floyd", "The Wall", "Money")
        self.assertIn("youtube.com/results", url)
        self.assertIn("search_query=", url)

    @patch("music.services.listening.find_bandcamp_url")
    def test_find_listen_url_prefers_bandcamp(self, mock_bandcamp):
        mock_bandcamp.return_value = "https://artist.bandcamp.com/track/demo"

        url, source = find_listen_url("A", "B", "C")

        self.assertEqual(source, "bandcamp")
        self.assertEqual(url, "https://artist.bandcamp.com/track/demo")

    @patch("music.services.listening.find_bandcamp_url")
    def test_find_listen_url_falls_back_to_youtube(self, mock_bandcamp):
        mock_bandcamp.return_value = None

        url, source = find_listen_url("Artist", "Album", "Track")

        self.assertEqual(source, "youtube")
        self.assertIn("youtube.com/results", url)


class AscoltaBranoViewTestCase(TestCase):
    def setUp(self):
        self.artista = Artista.objects.create(nome_artista="Pink Floyd")
        self.album = Album.objects.create(
            titolo_album="Wish You Were Here",
            artista_appartenenza=self.artista,
        )
        self.brano = Brano.objects.create(
            titolo_brano="Wish You Were Here",
            album_appartenenza=self.album,
        )
        self.client = Client()

    @patch("music.views.find_bandcamp_url")
    def test_redirects_to_bandcamp_when_found(self, mock_bandcamp):
        mock_bandcamp.return_value = "https://pinkfloyd.bandcamp.com/track/wish-you-were-here"

        response = self.client.get(reverse("ascolta_brano", kwargs={"pk": self.brano.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://pinkfloyd.bandcamp.com/track/wish-you-were-here")

    @patch("music.views.find_bandcamp_url")
    def test_renders_listen_page_with_youtube_fallback(self, mock_bandcamp):
        mock_bandcamp.return_value = None

        response = self.client.get(reverse("ascolta_brano", kwargs={"pk": self.brano.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ricerca del brano in corso")
        self.assertContains(response, "youtube.com/results")

    def test_album_page_shows_ascolta_button(self):
        response = self.client.get(reverse("album_view", kwargs={"pk": self.album.pk}))

        self.assertContains(response, "Ascolta")
        self.assertContains(response, reverse("ascolta_brano", kwargs={"pk": self.brano.pk}))
