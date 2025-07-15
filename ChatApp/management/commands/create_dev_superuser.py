from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
import os

class Command(BaseCommand):
    help = "Create a development superuser using DEV_ADMIN_EMAIL and DEV_ADMIN_PASSWORD env vars"

    def handle(self, *args, **options):
        if not settings.USE_DEV_AUTH:
            self.stderr.write("USE_DEV_AUTH must be enabled")
            return
        User = get_user_model()
        email = os.getenv('DEV_ADMIN_EMAIL', 'admin@example.com')
        password = os.getenv('DEV_ADMIN_PASSWORD', 'admin')
        if User.objects.filter(email=email).exists():
            self.stdout.write(f"User {email} already exists")
            return
        User.objects.create_superuser(email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Created dev superuser {email}"))
