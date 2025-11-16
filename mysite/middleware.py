"""
Middleware per eseguire migrazioni e creare superuser automaticamente su Render (piano Free)
"""
import os
import threading
from django.core.management import call_command
from django.db import connection
from django.contrib.auth import get_user_model

User = get_user_model()


class AutoMigrateMiddleware:
    """
    Esegue le migrazioni e crea un superuser automaticamente al primo accesso (solo su Render).
    Utile per il piano Free che non ha accesso alla Shell.
    """
    _initialized = False
    _lock = threading.Lock()

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Esegui migrazioni e crea superuser solo una volta, al primo accesso
        if not AutoMigrateMiddleware._initialized:
            with AutoMigrateMiddleware._lock:
                if not AutoMigrateMiddleware._initialized:
                    if os.environ.get('RENDER') or os.environ.get('DATABASE_URL'):
                        try:
                            connection.ensure_connection()
                            # Esegui migrazioni
                            call_command('migrate', '--noinput', verbosity=0)
                            
                            # Crea superuser se non esiste
                            self._create_superuser_if_needed()
                            
                            AutoMigrateMiddleware._initialized = True
                        except Exception as e:
                            # Se fallisce, continua comunque
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.warning(f"Errore durante inizializzazione automatica: {e}")

        return self.get_response(request)
    
    def _create_superuser_if_needed(self):
        """Crea un superuser se non esiste già"""
        # Controlla se esiste già un superuser
        if User.objects.filter(is_superuser=True).exists():
            return
        
        # Usa variabili d'ambiente o valori di default
        username = os.environ.get('SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('SUPERUSER_EMAIL', 'admin@example.com')
        password = os.environ.get('SUPERUSER_PASSWORD', 'admin123')
        
        # Crea il superuser
        try:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Superuser '{username}' creato automaticamente")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Errore durante creazione superuser: {e}")

