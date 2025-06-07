from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ChatApp", "0009_retentionpolicy"),
    ]

    operations = [
        migrations.CreateModel(
            name="MessageReceipt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("last_seen_id", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="ChatApp.conversation")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="ChatApp.customuser")),
            ],
            options={
                "unique_together": {("user", "conversation")},
            },
        ),
    ]
