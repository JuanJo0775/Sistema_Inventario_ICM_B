"""Modelo de configuración de datos fiscales de la empresa (CompanyInfo)."""

from __future__ import annotations

from django.db import models


class CompanyInfo(models.Model):
    """
    Singleton con los datos fiscales de la empresa para encabezados de factura.

    Solo debe existir un único registro (pk=1); el servicio lo garantiza via get_or_create.
    """

    company_name = models.CharField(
        max_length=200, default="Import Corporal Medical S.A.S"
    )
    nit = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    dian_resolution = models.TextField(blank=True)
    dian_range_from = models.PositiveIntegerField(null=True, blank=True)
    dian_range_to = models.PositiveIntegerField(null=True, blank=True)
    invoice_series = models.CharField(max_length=10, default="ICM")
    invoice_footer = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Información de empresa"
        verbose_name_plural = "Información de empresa"

    def __str__(self) -> str:
        return f"{self.company_name} (NIT {self.nit})"
