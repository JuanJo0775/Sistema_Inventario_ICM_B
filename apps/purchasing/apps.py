"""Configuración de la app purchasing (proveedores, OC, recepción)."""

from django.apps import AppConfig


class PurchasingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.purchasing"
    verbose_name = "Compras"
