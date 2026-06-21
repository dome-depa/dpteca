from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from music.models import Album, Artista, Brano
from music.services.brani_import import import_tracks_for_album
from music.services.musicbrainz import (
    ReleaseCandidate,
    TrackCandidate,
    format_duration,
    get_release_tracks,
    search_releases,
)


class MusicBrainzServiceTestCase(TestCase):
    @patch("music.services.musicbrainz._get")
    def test_search_releases_maps_response(self, mock_get):
        mock_get.return_value = {
            "releases": [
                {
                    "id": "release-1",
                    "title": "The Wall",
                    "date": "1979-11-30",
                    "country": "GB",
                    "track-count": 26,
                    "medium-count": 2,
                    "label-info": [{"label": {"name": "Harvest"}}],
                }
            ]
        }

        releases = search_releases("Pink Floyd", "The Wall", "1979-11-30")

        self.assertEqual(len(releases), 1)
        self.assertEqual(releases[0].mbid, "release-1")
        self.assertEqual(releases[0].label, "Harvest")
        mock_get.assert_called_once()

    @patch("music.services.musicbrainz._get")
    def test_get_release_tracks_maps_media(self, mock_get):
        mock_get.return_value = {
            "media": [
                {
                    "position": 1,
                    "tracks": [
                        {
                            "title": "In the Flesh?",
                            "number": "1",
                            "length": 199000,
                            "recording": {"artist-credit": [{"name": "Pink Floyd"}]},
                        }
                    ],
                }
            ]
        }

        tracks = get_release_tracks("release-1")

        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].titolo_brano, "In the Flesh?")
        self.assertEqual(tracks[0].sezione, "a")
        self.assertEqual(tracks[0].progressivo, "1")
        self.assertEqual(tracks[0].durata, "3:19")
        self.assertEqual(tracks[0].crediti, "Pink Floyd")

    def test_format_duration(self):
        self.assertEqual(format_duration(199000), "3:19")
        self.assertIsNone(format_duration(None))


class ImportBraniAlbumViewTestCase(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="staff",
            password="testpass123",
            is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username="regular",
            password="testpass123",
            is_staff=False,
        )
        self.artista = Artista.objects.create(nome_artista="Pink Floyd")
        self.album = Album.objects.create(
            titolo_album="The Wall",
            artista_appartenenza=self.artista,
            data_rilascio=date(1979, 11, 30),
        )
        self.client = Client()
        self.release = ReleaseCandidate(
            mbid="release-1",
            title="The Wall",
            date="1979-11-30",
            country="GB",
            label="Harvest",
            track_count=2,
            medium_count=1,
        )
        self.tracks = [
            TrackCandidate("In the Flesh?", "a", "1", "3:19", "Waters"),
            TrackCandidate("The Thin Ice", "a", "2", "2:27", "Waters"),
        ]

    @patch("music.views.get_release_tracks")
    @patch("music.views.search_releases")
    def test_staff_can_open_import_page(self, mock_search, mock_tracks):
        mock_search.return_value = [self.release]
        self.client.login(username="staff", password="testpass123")

        response = self.client.get(reverse("importa_brani_album", kwargs={"pk": self.album.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Importa brani da MusicBrainz")
        self.assertContains(response, "The Wall")

    def test_regular_user_denied(self):
        self.client.login(username="regular", password="testpass123")
        response = self.client.get(reverse("importa_brani_album", kwargs={"pk": self.album.pk}))
        self.assertIn(response.status_code, (302, 403))

    @patch("music.views.get_release_tracks")
    @patch("music.views.search_releases")
    def test_preview_selected_release(self, mock_search, mock_tracks):
        mock_search.return_value = [self.release]
        mock_tracks.return_value = self.tracks
        self.client.login(username="staff", password="testpass123")

        response = self.client.get(
            reverse("importa_brani_album", kwargs={"pk": self.album.pk}),
            {"release_mbid": "release-1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "In the Flesh?")
        self.assertContains(response, "Importa 2 brani")

    @patch("music.views.get_release_tracks")
    @patch("music.views.search_releases")
    def test_import_creates_tracks(self, mock_search, mock_tracks):
        mock_search.return_value = [self.release]
        mock_tracks.return_value = self.tracks
        self.client.login(username="staff", password="testpass123")

        response = self.client.post(
            reverse("importa_brani_album", kwargs={"pk": self.album.pk}),
            {"release_mbid": "release-1", "skip_existing": "on"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.album.brani.count(), 2)

    @patch("music.views.get_release_tracks")
    @patch("music.views.search_releases")
    def test_import_skips_existing_tracks(self, mock_search, mock_tracks):
        Brano.objects.create(
            titolo_brano="In the Flesh?",
            sezione="a",
            progressivo="1",
            album_appartenenza=self.album,
        )
        mock_search.return_value = [self.release]
        mock_tracks.return_value = self.tracks
        self.client.login(username="staff", password="testpass123")

        response = self.client.post(
            reverse("importa_brani_album", kwargs={"pk": self.album.pk}),
            {"release_mbid": "release-1", "skip_existing": "on"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.album.brani.count(), 2)
        messages = [str(message) for message in response.context["messages"]]
        self.assertTrue(any("1 creati" in message for message in messages))
        self.assertTrue(any("1 saltati" in message for message in messages))

    def test_import_tracks_for_album_service(self):
        tracks = [
            TrackCandidate("Track A", "a", "1", "3:00", None),
            TrackCandidate("Track B", "a", "2", "4:00", None),
        ]
        result = import_tracks_for_album(self.album, tracks)
        self.assertEqual(result.created, 2)
        self.assertEqual(self.album.brani.count(), 2)
