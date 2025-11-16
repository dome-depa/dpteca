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
        from django.core.management import execute_from_command_line
        import sys
        # Controlla se ci sono migrazioni pendenti ed eseguile
        from django.db import connection
        from django.core.management import call_command
        # Esegui le migrazioni in modo silenzioso
        call_command('migrate', '--noinput', verbosity=0)
    except Exception:
        # Se fallisce, ignora e continua (l'app partirà comunque)
        pass

application = get_wsgi_application()
