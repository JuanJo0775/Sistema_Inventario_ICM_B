"""Modelo de usuario ICM (RF-001, RF-002, BR-01, BR-02, BR-03)."""

from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class RoleChoices(models.TextChoices):
    """Roles RBAC del sistema (BR-01, BR-02)."""

    ALMACENISTA = "almacenista", "Almacenista"
    AUXILIAR_DESPACHO = "auxiliar_despacho", "Auxiliar de despacho"
    ADMINISTRADOR = "administrador", "Administrador"


# Alias retrocompatible con código existente
UserRole = RoleChoices


class User(AbstractUser):
    """
    Usuario del sistema con RBAC (RF-001, RF-002).

    `is_active` habilita o deshabilita la cuenta (BR-02).
    `created_by` registra el almacenista que creó la cuenta (BR-01).

    `email` es obligatorio y único (contacto institucional y login alternativo a username).
    Nota: El campo `password` (y el manejo de hashing seguro) es proveído nativamente
    al heredar de `AbstractUser`, por lo que no es necesario redeclararlo aquí.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField("correo electrónico", unique=True, blank=False)
    role = models.CharField(max_length=32, choices=RoleChoices.choices)
    created_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_users",
    )
    phone = models.CharField(max_length=20, blank=True)  # contacto opcional
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ("username",)

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"


class UserSchedule(models.Model):
    """
    Horario personalizado y estable para un Auxiliar de Despacho (reemplaza horario por defecto).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="custom_schedule",
    )
    morning_start = models.TimeField(null=True, blank=True)
    morning_end = models.TimeField(null=True, blank=True)
    afternoon_start = models.TimeField(null=True, blank=True)
    afternoon_end = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Horario de Usuario"
        verbose_name_plural = "Horarios de Usuarios"
        indexes = [
            models.Index(fields=("user", "is_active")),
        ]

    def clean(self) -> None:
        super().clean()
        if hasattr(self, "user") and self.user and self.user.role != "auxiliar_despacho":
            raise ValidationError(
                "Solo se puede asignar un horario personalizado a auxiliares de despacho."
            )

        if (self.morning_start and not self.morning_end) or (
            not self.morning_start and self.morning_end
        ):
            raise ValidationError(
                "Debe especificar inicio y fin de la franja de la mañana."
            )
        if (self.afternoon_start and not self.afternoon_end) or (
            not self.afternoon_start and self.afternoon_end
        ):
            raise ValidationError(
                "Debe especificar inicio y fin de la franja de la tarde."
            )

        if (
            self.morning_start
            and self.morning_end
            and self.morning_start >= self.morning_end
        ):
            raise ValidationError(
                "La hora de inicio de la mañana debe ser anterior a la de fin."
            )
        if (
            self.afternoon_start
            and self.afternoon_end
            and self.afternoon_start >= self.afternoon_end
        ):
            raise ValidationError(
                "La hora de inicio de la tarde debe ser anterior a la de fin."
            )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Schedule for {self.user.username} (Active: {self.is_active})"


class TemporaryAccessPermit(models.Model):
    """
    Exclusión horaria temporal para un Auxiliar de Despacho (excepción operativa por fechas).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="temporary_permits",
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    allow_24_7 = models.BooleanField(default=False)
    custom_morning_start = models.TimeField(null=True, blank=True)
    custom_morning_end = models.TimeField(null=True, blank=True)
    custom_afternoon_start = models.TimeField(null=True, blank=True)
    custom_afternoon_end = models.TimeField(null=True, blank=True)
    reason = models.TextField()
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="granted_permits",
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Permiso Temporal de Acceso"
        verbose_name_plural = "Permisos Temporales de Acceso"
        indexes = [
            models.Index(fields=("user", "is_active", "start_datetime", "end_datetime")),
        ]

    def clean(self) -> None:
        super().clean()
        if hasattr(self, "user") and self.user and self.user.role != "auxiliar_despacho":
            raise ValidationError(
                "Solo se pueden otorgar permisos temporales a auxiliares de despacho."
            )

        if (
            self.start_datetime
            and self.end_datetime
            and self.start_datetime >= self.end_datetime
        ):
            raise ValidationError(
                "La fecha/hora de fin debe ser posterior a la de inicio."
            )

        if not self.reason or not self.reason.strip():
            raise ValidationError("El motivo de la autorización es obligatorio.")

        if not self.allow_24_7:
            # Must define at least one custom range
            has_morning = self.custom_morning_start and self.custom_morning_end
            has_afternoon = self.custom_afternoon_start and self.custom_afternoon_end
            if not has_morning and not has_afternoon:
                raise ValidationError(
                    "Si no se permite acceso 24/7, debe configurar al menos una franja horaria válida (mañana o tarde)."
                )

        if (self.custom_morning_start and not self.custom_morning_end) or (
            not self.custom_morning_start and self.custom_morning_end
        ):
            raise ValidationError(
                "Debe especificar inicio y fin de la franja custom de la mañana."
            )
        if (self.custom_afternoon_start and not self.custom_afternoon_end) or (
            not self.custom_afternoon_start and self.custom_afternoon_end
        ):
            raise ValidationError(
                "Debe especificar inicio y fin de la franja custom de la tarde."
            )

        if (
            self.custom_morning_start
            and self.custom_morning_end
            and self.custom_morning_start >= self.custom_morning_end
        ):
            raise ValidationError(
                "La hora de inicio de la mañana debe ser anterior a la de fin."
            )
        if (
            self.custom_afternoon_start
            and self.custom_afternoon_end
            and self.custom_afternoon_start >= self.custom_afternoon_end
        ):
            raise ValidationError(
                "La hora de inicio de la tarde debe ser anterior a la de fin."
            )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Permit for {self.user.username} (Active: {self.is_active}, 24/7: {self.allow_24_7})"
