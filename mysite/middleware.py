"""
Middleware per eseguire migrazioni automaticamente su Render (piano Free)
"""
import os
import threading
from django.core.management import call_command
from django.db import connection


class AutoMigrateMiddleware:
    """
    Esegue le migrazioni automaticamente al primo accesso (solo su Render).
    Utile per il piano Free che non ha accesso alla Shell.
    """
    _migrated = False
    _lock = threading.Lock()

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Esegui migrazioni solo una volta, al primo accesso
        if not AutoMigrateMiddleware._migrated:
            with AutoMigrateMiddleware._lock:
                if not AutoMigrateMiddleware._migrated:
                    if os.environ.get('RENDER') or os.environ.get('DATABASE_URL'):
                        try:
                            connection.ensure_connection()
                            call_command('migrate', '--noinput', verbosity=0)
                            AutoMigrateMiddleware._migrated = True
                        except Exception as e:
                            # Se fallisce, continua comunque
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.warning(f"Errore durante migrazioni automatiche: {e}")

        return self.get_response(request)

