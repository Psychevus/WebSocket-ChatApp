from django.core.management.base import BaseCommand, CommandError
from django.core import serializers
from django.db.models import Q
import json
import zipfile
from io import BytesIO

from ChatApp.models import CustomUser, Conversation, Message, MessageReceipt


class Command(BaseCommand):
    help = "Export a user's data to a zip file"

    def add_arguments(self, parser):
        parser.add_argument('email')

    def handle(self, email, **options):
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise CommandError('User not found')

        convs = Conversation.objects.filter(Q(user1=user) | Q(user2=user))
        messages = Message.objects.filter(conversation__in=convs)
        receipts = MessageReceipt.objects.filter(user=user)

        data = {
            'profile': json.loads(serializers.serialize('json', [user]))[0],
            'messages': json.loads(serializers.serialize('json', messages)),
            'receipts': json.loads(serializers.serialize('json', receipts)),
        }

        buf = BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('data.json', json.dumps(data, indent=2))
        filename = f'user_{user.id}_data.zip'
        with open(filename, 'wb') as fh:
            fh.write(buf.getvalue())
        self.stdout.write(self.style.SUCCESS(f'Exported {filename}'))
