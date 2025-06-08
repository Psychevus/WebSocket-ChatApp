from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('ChatApp', '0012_device_tokens'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='pending_erasure',
            field=models.BooleanField(default=False),
        ),
    ]
