from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ChatApp', '0003_conversation_retention'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='expires_at',
            field=models.DateTimeField(null=True, blank=True, help_text='When to permanently delete this message'),
        ),
    ]
