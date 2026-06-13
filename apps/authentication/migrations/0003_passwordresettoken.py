# Generated migration — adds PasswordResetToken model (RF-001: self-service password recovery)

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0002_userschedule_temporaryaccesspermit"),
    ]

    operations = [
        migrations.CreateModel(
            name="PasswordResetToken",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("expires_at", models.DateTimeField()),
                ("used", models.BooleanField(default=False)),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="password_reset_tokens",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Token de recuperación de contraseña",
                "verbose_name_plural": "Tokens de recuperación de contraseña",
                "indexes": [
                    models.Index(
                        fields=["token_hash"],
                        name="authenticat_token_h_idx",
                    ),
                    models.Index(
                        fields=["user", "used", "expires_at"],
                        name="authenticat_user_used_expires_idx",
                    ),
                ],
            },
        ),
    ]
