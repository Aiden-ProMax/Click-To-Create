#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Load .env before any Django imports
from dotenv import load_dotenv
load_dotenv()

# Allow OAuth over HTTP in development (localhost only)
if os.getenv('OAUTHLIB_INSECURE_TRANSPORT', '').lower() == 'true':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autoplanner.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
