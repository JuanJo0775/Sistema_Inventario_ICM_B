"""Modelo de usuario ICM (RF-001, RF-002, BR-01, BR-02, BR-03)."""

from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractUser
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
