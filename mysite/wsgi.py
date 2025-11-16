"""
WSGI config for mysite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# Esegui migrazioni automaticamente all'avvio (solo su Render, se necessario)
# Questo è utile per il piano Free che non ha accesso alla Shell
if os.environ.get('RENDER') or os.environ.get('DATABASE_URL'):
    try:
        from django.core.management import call_command
        from django.db import connection
        # Verifica che il database sia accessibile
        connection.ensure_connection()
        # Esegui le migrazioni
        call_command('migrate', '--noinput', verbosity=1)
    except Exception as e:
        # Log dell'errore ma continua (l'app partirà comunque)
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Errore durante migrazioni automatiche: {e}")

application = get_wsgi_application()
