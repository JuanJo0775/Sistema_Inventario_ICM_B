"""Ledger central de movimientos (RF-005–RF-009, BR-10, BR-11, BR-13)."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class MovementType(models.TextChoices):
    ENTRADA = "ENTRADA", "Entrada"
    SALIDA_VENTA_MAYOR = "SALIDA_VENTA_MAYOR", "Salida venta mayor"
    SALIDA_VENTA_MENOR = "SALIDA_VENTA_MENOR", "Salida venta menor"
    SALIDA_DANO = "SALIDA_DANO", "Salida por daño"
    SALIDA_VENCIMIENTO = "SALIDA_VENCIMIENTO", "Salida por vencimiento"
    TRASLADO = "TRASLADO", "Traslado interno"
    AJUSTE = "AJUSTE", "Ajuste"
    DEVOLUCION = "DEVOLUCION", "Devolución"
    SALIDA_COMBO = "SALIDA_COMBO", "Salida por combo"


class Movement(models.Model):
    """
    LEDGER — fuente de verdad del inventario (BR-10, BR-11).

    Inmutable por diseño: sin `updated_at`; la API no expone mutación del historial.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    movement_type = models.CharField(max_length=32, choices=MovementType.choices)

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="movements",
    )
    lot = models.ForeignKey(
        "catalog.Lot",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="movements",
    )
    origin_location = models.ForeignKey(
        "inventory.Location",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="outgoing_movements",
    )
    destination_location = models.ForeignKey(
        "inventory.Location",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="incoming_movements",
    )

    quantity = models.PositiveIntegerField()
    stock_previo_origen = models.PositiveIntegerField(null=True, blank=True)
    stock_resultante_origen = models.PositiveIntegerField(null=True, blank=True)
    stock_previo_destino = models.PositiveIntegerField(null=True, blank=True)
    stock_resultante_destino = models.PositiveIntegerField(null=True, blank=True)

    serial_number = models.CharField(max_length=100, null=True, blank=True)  # BR-04
    quantity_invoiced = models.PositiveIntegerField(null=True, blank=True)  # BR-09
    discrepancy_note = models.TextField(null=True, blank=True)  # BR-09
    justification = models.TextField(null=True, blank=True)  # BR-07

    scanned_code = models.CharField(max_length=100, null=True, blank=True)  # BR-08
    order_sku = models.CharField(max_length=100, null=True, blank=True)  # BR-08

    invoice_number = models.CharField(max_length=20, null=True, blank=True)  # BR-13
    invoice_pdf = models.FileField(
        upload_to="invoices/%Y/%m/", null=True, blank=True
    )  # BR-13

    # --- Snapshot de precio congelado al momento del despacho ---
    # Todos nullable: movimientos históricos quedan sin precio (documentado por diseño).
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Precio unitario de venta congelado al momento del despacho.",
    )
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Costo unitario congelado al momento del despacho.",
    )
    discount_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Porcentaje de descuento aplicado (0-100).",
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Monto de descuento calculado.",
    )
    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="unit_price × quantity.",
    )
    tax_rate_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Tasa de IVA congelada al momento del despacho.",
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Monto de IVA calculado sobre la base imponible.",
    )
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Total a cobrar: subtotal - discount_amount + tax_amount.",
    )
    currency = models.CharField(
        max_length=3,
        null=True,
        blank=True,
        help_text="Moneda ISO 4217 del despacho.",
    )
    price_type = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Tipo de precio: retail | wholesale | cost | combo.",
    )
    customer_snapshot = models.JSONField(
        null=True,
        blank=True,
        help_text="Datos del cliente al momento del despacho (R-02).",
    )

    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="movements_executed",
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    related_movement = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="correction_links",
    )

    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("product", "movement_type", "created_at")),
            models.Index(fields=("executed_by", "created_at")),
            models.Index(fields=("origin_location", "created_at")),
            models.Index(fields=("destination_location", "created_at")),
            models.Index(fields=("invoice_number",)),
            models.Index(fields=("lot",), name="movements_movement_lot_idx"),
            models.Index(fields=("product", "lot"), name="movements_mov_prod_lot_idx"),
            models.Index(fields=("product", "origin_location")),
            models.Index(fields=("product", "destination_location")),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("invoice_number",),
                condition=Q(invoice_number__isnull=False) & ~Q(invoice_number=""),
                name="uniq_movement_invoice_number_when_set",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.movement_type} {self.product_id} qty={self.quantity}"


class InvoiceCounter(models.Model):
    """
    Numeración secuencial atómica de facturas (BR-13).

    Singleton: un único registro; `movements.services` usa select_for_update().
    """

    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Contador de factura"
        verbose_name_plural = "Contadores de factura"

    def __str__(self) -> str:
        return f"ICM last={self.last_number}"


class Invoice(models.Model):
    """
    Encabezado de factura comercial — agrupa uno o varios Movements bajo un número de comprobante.

    Permite reconstruir el documento comercial completo sin depender de datos mutables del producto.
    """

    number = models.CharField(max_length=20, unique=True, help_text="Número ICM-XXXX.")
    movements = models.ManyToManyField(
        Movement,
        related_name="invoices",
        blank=True,
    )
    customer_name = models.CharField(max_length=255, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=50, blank=True)
    customer_address = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    discount_total = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    tax_total = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    currency = models.CharField(max_length=3, default="COP")

    pdf = models.FileField(upload_to="invoices/%Y/%m/", null=True, blank=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="invoices_issued",
    )
    issued_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ("-issued_at",)
        indexes = [
            models.Index(fields=("number",)),
            models.Index(fields=("issued_at",)),
        ]

    def __str__(self) -> str:
        return f"Factura {self.number}"
