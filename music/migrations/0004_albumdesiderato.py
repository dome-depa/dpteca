from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("music", "0003_alter_brano_progressivo_alter_brano_titolo_brano"),
    ]

    operations = [
        migrations.CreateModel(
            name="AlbumDesiderato",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titolo_album", models.CharField(max_length=140)),
                ("copertina", models.ImageField(blank=True, null=True, upload_to="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("artista", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="album_desiderati", to="music.artista")),
            ],
            options={
                "verbose_name": "Album desiderato",
                "verbose_name_plural": "Album desiderati",
                "ordering": ["artista__nome_artista", "titolo_album", "copertina"],
            },
        ),
    ]
