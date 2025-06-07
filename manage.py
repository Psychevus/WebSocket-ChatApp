#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import collections
from collections import abc as collections_abc

if not hasattr(collections, "MutableSet"):
    collections.MutableSet = collections_abc.MutableSet
if not hasattr(collections, "MutableMapping"):
    collections.MutableMapping = collections_abc.MutableMapping
if not hasattr(collections, "MutableSequence"):
    collections.MutableSequence = collections_abc.MutableSequence


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WebSocketChatApp.settings')
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
