from unittest.mock import patch

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from music.models import Album, Artista, Brano
from music.services.listening import (
    cache_listen_url,
    find_bandcamp_url,
    find_youtube_watch_url,
    resolve_listen_url,
    youtube_search_url,
)


class ListeningServiceTestCase(TestCase):
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

    @override_settings(YOUTUBE_API_KEY="test-key")
    @patch("music.services.listening.requests.get")
    def test_find_youtube_watch_url(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
            "items": [{"id": {"videoId": "abc123XYZ"}}]
        }

        url = find_youtube_watch_url("Pink Floyd", "The Wall", "Money")

        self.assertEqual(url, "https://www.youtube.com/watch?v=abc123XYZ")
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["key"], "test-key")

    @override_settings(YOUTUBE_API_KEY="")
    def test_find_youtube_watch_url_without_api_key(self):
        self.assertIsNone(find_youtube_watch_url("A", "B", "C"))

    @patch("music.services.listening.find_youtube_watch_url")
    @patch("music.services.listening.find_bandcamp_url")
    def test_resolve_prefers_youtube_watch_when_no_bandcamp(self, mock_bandcamp, mock_youtube):
        mock_bandcamp.return_value = None
        mock_youtube.return_value = "https://www.youtube.com/watch?v=abc123"

        url, source, from_cache = resolve_listen_url(self.brano)

        self.brano.refresh_from_db()
        self.assertFalse(from_cache)
        self.assertEqual(source, "youtube")
        self.assertEqual(url, "https://www.youtube.com/watch?v=abc123")
        self.assertEqual(self.brano.ascolto_url, url)

    @patch("music.services.listening.find_bandcamp_url")
    def test_resolve_caches_bandcamp_url(self, mock_bandcamp):
        mock_bandcamp.return_value = "https://pinkfloyd.bandcamp.com/track/wish-you-were-here"

        url, source, from_cache = resolve_listen_url(self.brano)

        self.brano.refresh_from_db()
        self.assertFalse(from_cache)
        self.assertEqual(source, "bandcamp")
        self.assertEqual(url, "https://pinkfloyd.bandcamp.com/track/wish-you-were-here")
        self.assertEqual(self.brano.ascolto_url, url)
        self.assertEqual(self.brano.ascolto_fonte, "bandcamp")

    @patch("music.services.listening.find_youtube_watch_url")
    @patch("music.services.listening.find_bandcamp_url")
    def test_resolve_uses_cache(self, mock_bandcamp, mock_youtube):
        cache_listen_url(
            self.brano,
            "https://www.youtube.com/watch?v=cached",
            Brano.ASCOLTO_FONTE_YOUTUBE,
        )

        url, source, from_cache = resolve_listen_url(self.brano)

        self.assertTrue(from_cache)
        self.assertEqual(url, "https://www.youtube.com/watch?v=cached")
        self.assertEqual(source, "youtube")
        mock_bandcamp.assert_not_called()
        mock_youtube.assert_not_called()

    @patch("music.services.listening.find_youtube_watch_url")
    @patch("music.services.listening.find_bandcamp_url")
    def test_resolve_refresh_bypasses_cache(self, mock_bandcamp, mock_youtube):
        cache_listen_url(
            self.brano,
            "https://www.youtube.com/watch?v=old",
            Brano.ASCOLTO_FONTE_YOUTUBE,
        )
        mock_bandcamp.return_value = None
        mock_youtube.return_value = "https://www.youtube.com/watch?v=new"

        url, source, from_cache = resolve_listen_url(self.brano, refresh=True)

        self.brano.refresh_from_db()
        self.assertFalse(from_cache)
        self.assertEqual(url, "https://www.youtube.com/watch?v=new")
        self.assertEqual(self.brano.ascolto_url, url)

    @patch("music.services.listening.find_youtube_watch_url")
    @patch("music.services.listening.find_bandcamp_url")
    def test_resolve_does_not_cache_search_url(self, mock_bandcamp, mock_youtube):
        mock_bandcamp.return_value = None
        mock_youtube.return_value = None

        url, source, from_cache = resolve_listen_url(self.brano)

        self.brano.refresh_from_db()
        self.assertFalse(from_cache)
        self.assertIn("youtube.com/results", url)
        self.assertIsNone(self.brano.ascolto_url)
        self.assertIsNone(self.brano.ascolto_fonte)


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

    @patch("music.views.resolve_listen_url")
    def test_redirects_to_resolved_url(self, mock_resolve):
        mock_resolve.return_value = (
            "https://pinkfloyd.bandcamp.com/track/wish-you-were-here",
            "bandcamp",
            False,
        )

        response = self.client.get(reverse("ascolta_brano", kwargs={"pk": self.brano.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://pinkfloyd.bandcamp.com/track/wish-you-were-here")

    @patch("music.views.resolve_listen_url")
    def test_refresh_query_param(self, mock_resolve):
        mock_resolve.return_value = (
            "https://www.youtube.com/watch?v=abc",
            "youtube",
            False,
        )

        response = self.client.get(
            reverse("ascolta_brano", kwargs={"pk": self.brano.pk}),
            {"refresh": "1"},
        )

        self.assertEqual(response.status_code, 302)
        mock_resolve.assert_called_once()
        _, kwargs = mock_resolve.call_args
        self.assertTrue(kwargs.get("refresh"))

    def test_album_page_shows_ascolta_button(self):
        response = self.client.get(reverse("album_view", kwargs={"pk": self.album.pk}))

        self.assertContains(response, "Ascolta")
        self.assertContains(response, reverse("ascolta_brano", kwargs={"pk": self.brano.pk}))
