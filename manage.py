#!/usr/bin/env python
<<<<<<< HEAD
=======
"""Django's command-line utility for administrative tasks."""
>>>>>>> 8c142e1c3888d30903d3e352271c439708bfc593
import os
import sys


def main():
<<<<<<< HEAD
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nagarawa.settings')
=======
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
>>>>>>> 8c142e1c3888d30903d3e352271c439708bfc593
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
<<<<<<< HEAD
            "Couldn't import Django. Are you sure it's installed?"
=======
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
>>>>>>> 8c142e1c3888d30903d3e352271c439708bfc593
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
