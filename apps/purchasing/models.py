"""Proveedores, Órdenes de Compra y Recepción de mercancía."""

from django.conf import settings
from django.db import models
from django.db.models import Q

from shared.models import BaseModel, SoftDeleteModel


class Supplier(BaseModel, SoftDeleteModel):
    """Proveedor de mercancía. Su activación/desactivación no afecta OC existentes."""

    nombre_comercial = models.CharField(max_length=200)
    razon_social = models.CharField(max_length=200)
    nit = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text="NIT del proveedor incluyendo dígito de verificación.",
    )
    pais = models.CharField(max_length=100)
    correo = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    direccion = models.CharField(max_length=300, blank=True)
    is_active = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="suppliers_created",
    )

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ("nombre_comercial",)
        indexes = [
            models.Index(fields=("nit",)),
            models.Index(fields=("is_active", "nombre_comercial")),
        ]

    def __str__(self) -> str:
        return (
            f"{self.nombre_comercial} ({self.nit})"
            if self.nit
            else self.nombre_comercial
        )


class PurchaseOrderStatus(models.TextChoices):
    BORRADOR = "borrador", "Borrador"
    PENDIENTE = "pendiente", "Pendiente"
    PARCIALMENTE_RECIBIDA = "parcialmente_recibida", "Parcialmente recibida"
    COMPLETADA = "completada", "Completada"
    CANCELADA = "cancelada", "Cancelada"


class PurchaseOrderCounter(models.Model):
    """Singleton para numeración secuencial atómica de OC (igual que InvoiceCounter)."""

    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Contador de OC"
        verbose_name_plural = "Contadores de OC"

    def __str__(self) -> str:
        return f"OC last={self.last_number}"


class PurchaseOrder(BaseModel):
    """
    Orden de Compra — representa la expectativa de recepción de mercancía.

    NO genera stock por sí misma. El stock se actualiza únicamente cuando
    una Reception asociada es confirmada y genera Movements de tipo ENTRADA.
    """

    number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Número secuencial OC-XXXX, generado automáticamente.",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )
    status = models.CharField(
        max_length=30,
        choices=PurchaseOrderStatus.choices,
        default=PurchaseOrderStatus.BORRADOR,
    )
    expected_delivery = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha estimada de llegada de la mercancía.",
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="purchase_orders_created",
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="purchase_orders_confirmed",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="purchase_orders_cancelled",
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        verbose_name = "Orden de Compra"
        verbose_name_plural = "Órdenes de Compra"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("status", "created_at")),
            models.Index(fields=("supplier", "status")),
            models.Index(fields=("number",)),
        ]

    def __str__(self) -> str:
        return f"OC {self.number} [{self.status}]"

    @property
    def is_editable(self) -> bool:
        return self.status == PurchaseOrderStatus.BORRADOR

    @property
    def is_receivable(self) -> bool:
        return self.status in (
            PurchaseOrderStatus.PENDIENTE,
            PurchaseOrderStatus.PARCIALMENTE_RECIBIDA,
        )


class PurchaseOrderItem(BaseModel):
    """Ítem de línea de una OC. Inmutable una vez que la OC pasa a PENDIENTE."""

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="purchase_order_items",
    )
    quantity_ordered = models.PositiveIntegerField(
        help_text="Cantidad solicitada al proveedor.",
    )
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Costo unitario acordado con el proveedor.",
    )
    notes = models.CharField(max_length=300, blank=True)
    quantity_received = models.PositiveIntegerField(
        default=0,
        help_text="Acumulado de unidades recibidas en recepciones confirmadas.",
    )

    class Meta:
        verbose_name = "Ítem de OC"
        verbose_name_plural = "Ítems de OC"
        constraints = [
            models.UniqueConstraint(
                fields=["purchase_order", "product"],
                name="uniq_po_item_product",
            ),
            models.CheckConstraint(
                condition=Q(quantity_ordered__gt=0),
                name="poi_qty_ordered_positive",
            ),
            models.CheckConstraint(
                condition=Q(quantity_received__gte=0),
                name="poi_qty_received_nonneg",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product} × {self.quantity_ordered} (OC {self.purchase_order.number})"

    @property
    def quantity_pending(self) -> int:
        return max(0, self.quantity_ordered - self.quantity_received)

    @property
    def is_fully_received(self) -> bool:
        return self.quantity_received >= self.quantity_ordered


class ReceptionStatus(models.TextChoices):
    BORRADOR = "borrador", "Borrador"
    CONFIRMADA = "confirmada", "Confirmada"
    CANCELADA = "cancelada", "Cancelada"


class Reception(BaseModel):
    """
    Recepción física de mercancía asociada a una OC.

    En estado BORRADOR: editable, sin efecto en inventario.
    En estado CONFIRMADA: inmutable, ha generado Movements de tipo ENTRADA.
    """

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        related_name="receptions",
    )
    status = models.CharField(
        max_length=15,
        choices=ReceptionStatus.choices,
        default=ReceptionStatus.BORRADOR,
    )
    destination_location = models.ForeignKey(
        "inventory.Location",
        on_delete=models.PROTECT,
        related_name="receptions",
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="receptions_received",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Recepción"
        verbose_name_plural = "Recepciones"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("purchase_order", "status")),
            models.Index(fields=("received_by", "confirmed_at")),
        ]

    def __str__(self) -> str:
        return f"Recepción {self.id} [{self.status}] OC={self.purchase_order.number}"

    @property
    def is_editable(self) -> bool:
        return self.status == ReceptionStatus.BORRADOR


class ReceptionItem(BaseModel):
    """
    Ítem de línea de una Recepción.

    Al confirmar la recepción, movement se enlaza al Movement ENTRADA generado
    por movements.services.register_entry() en el modo simple. En el modo avanzado,
    las porciones distribuidas se registran en ReceptionItemAllocation.
    """

    reception = models.ForeignKey(
        Reception,
        on_delete=models.CASCADE,
        related_name="items",
    )
    purchase_order_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.PROTECT,
        related_name="reception_items",
    )
    quantity_received = models.PositiveIntegerField()
    lot_code = models.CharField(max_length=100, blank=True)
    lot_expiration_date = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de vencimiento del lote recibido.",
    )
    serial_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="BR-04: Número de serie (obligatorio si la categoría lo exige).",
    )
    discrepancy_note = models.TextField(
        blank=True,
        help_text="Obligatorio cuando la cantidad recibida difiere de la esperada.",
    )
    movement = models.OneToOneField(
        "movements.Movement",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reception_item_link",
        help_text="Movimiento ENTRADA generado al confirmar la recepción.",
    )

    class Meta:
        verbose_name = "Ítem de Recepción"
        verbose_name_plural = "Ítems de Recepción"
        constraints = [
            models.UniqueConstraint(
                fields=["reception", "purchase_order_item"],
                name="uniq_reception_item",
            ),
            models.CheckConstraint(
                condition=Q(quantity_received__gte=0),
                name="ri_qty_received_nonneg",
            ),
        ]

    def __str__(self) -> str:
        return f"ReceptionItem {self.id} qty={self.quantity_received}"

    @property
    def quantity_expected(self) -> int:
        return self.purchase_order_item.quantity_pending

    @property
    def has_discrepancy(self) -> bool:
        return self.quantity_received != self.quantity_expected


class ReceptionItemAllocation(BaseModel):
    """
    Porción distribuida de un ítem de recepción.

    Permite segregar una cantidad recibida por lote y por ubicación sin romper el
    flujo simple existente de Reception/ReceptionItem.
    """

    reception_item = models.ForeignKey(
        ReceptionItem,
        on_delete=models.CASCADE,
        related_name="allocations",
    )
    location = models.ForeignKey(
        "inventory.Location",
        on_delete=models.PROTECT,
        related_name="reception_item_allocations",
    )
    quantity_received = models.PositiveIntegerField()
    lot_code = models.CharField(max_length=100, blank=True, null=True)
    lot_expiration_date = models.DateField(null=True, blank=True)
    serial_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="BR-04: Número de serie (obligatorio si la categoría lo exige).",
    )
    movement = models.OneToOneField(
        "movements.Movement",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reception_allocation_link",
        help_text="Movimiento ENTRADA generado para esta porción de recepción.",
    )

    class Meta:
        verbose_name = "Distribución de ítem de recepción"
        verbose_name_plural = "Distribuciones de ítems de recepción"
        ordering = ("created_at", "id")
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity_received__gt=0),
                name="ria_qty_received_positive",
            ),
        ]

    def __str__(self) -> str:
        lot = self.lot_code or "sin lote"
        return (
            f"{self.reception_item_id} -> {self.location_id} "
            f"({lot}, qty={self.quantity_received})"
        )
