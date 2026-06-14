"""Implementaciones Gherkin — RF019-RF025 (Módulo de compras)."""

from __future__ import annotations

from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditEventType, AuditLog
from apps.purchasing.models import PurchaseOrderStatus, ReceptionStatus

# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _supplier_payload(**overrides) -> dict:
    base = {
        "nombre_comercial": "Proveedor ICM Test",
        "razon_social": "Proveedor ICM Test S.A.S.",
        "nit": "900111222-1",
        "pais": "Colombia",
        "correo": "contacto@proveedoricm.com",
        "telefono": "3001234567",
        "ciudad": "Bogotá",
    }
    base.update(overrides)
    return base


def _create_supplier_via_api(client: APIClient, **overrides) -> dict:
    r = client.post(
        reverse("supplier-list-create"),
        _supplier_payload(**overrides),
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED, r.data
    return r.data


def _create_po_via_api(
    client: APIClient, supplier_id: str, product_id: str, **overrides
) -> dict:
    payload = {
        "supplier_id": supplier_id,
        "items": [
            {
                "product_id": product_id,
                "quantity_ordered": overrides.pop("quantity_ordered", 10),
                "unit_cost": str(overrides.pop("unit_cost", "15000.0000")),
            }
        ],
        **overrides,
    }
    r = client.post(reverse("po-list-create"), payload, format="json")
    assert r.status_code == status.HTTP_201_CREATED, r.data
    return r.data


def _confirm_po(client: APIClient, po_id: str) -> dict:
    r = client.post(reverse("po-confirm", kwargs={"pk": po_id}))
    assert r.status_code == status.HTTP_200_OK, r.data
    return r.data


def _create_reception_via_api(
    client: APIClient,
    po_id: str,
    poi_id: str,
    location_id: str,
    quantity: int = 5,
    discrepancy_note: str = "",
) -> dict:
    payload = {
        "po_id": po_id,
        "destination_location_id": location_id,
        "items": [
            {
                "purchase_order_item_id": poi_id,
                "quantity_received": quantity,
                "discrepancy_note": discrepancy_note,
            }
        ],
    }
    r = client.post(reverse("reception-list-create"), payload, format="json")
    assert r.status_code == status.HTTP_201_CREATED, r.data
    return r.data


def _confirm_reception(client: APIClient, reception_id: str) -> dict:
    r = client.post(reverse("reception-confirm", kwargs={"pk": reception_id}))
    assert r.status_code == status.HTTP_200_OK, r.data
    return r.data


# ---------------------------------------------------------------------------
# RF-019 — Gestión de proveedores
# ---------------------------------------------------------------------------


def impl_rf019_s01(authenticated_almacenista_client: APIClient, db):
    """Creación de proveedor con NIT único."""
    r = authenticated_almacenista_client.post(
        reverse("supplier-list-create"),
        _supplier_payload(nit="800100200-3"),
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED
    assert r.data["nit"] == "800100200-3"
    assert r.data["is_active"] is True
    assert AuditLog.objects.filter(event_type=AuditEventType.SUPPLIER_CREATED).exists()


def impl_rf019_s02(authenticated_almacenista_client: APIClient, db):
    """Intento de crear proveedor con NIT duplicado — BR-018."""
    _create_supplier_via_api(authenticated_almacenista_client, nit="800111222-9")
    r = authenticated_almacenista_client.post(
        reverse("supplier-list-create"),
        _supplier_payload(
            nombre_comercial="Otro Proveedor",
            nit="800111222-9",
        ),
        format="json",
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    from apps.purchasing.models import Supplier

    assert Supplier.objects.filter(nit="800111222-9").count() == 1


def impl_rf019_s03(authenticated_almacenista_client: APIClient, db):
    """Desactivación de proveedor — el registro persiste, solo cambia is_active."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="900222333-5"
    )
    r = authenticated_almacenista_client.post(
        reverse("supplier-deactivate", kwargs={"pk": supplier["id"]})
    )
    assert r.status_code == status.HTTP_200_OK
    assert r.data["is_active"] is False
    from apps.purchasing.models import Supplier

    assert Supplier.objects.filter(pk=supplier["id"]).exists()
    assert AuditLog.objects.filter(
        event_type=AuditEventType.SUPPLIER_SOFT_DELETED
    ).exists()


def impl_rf019_s04(almacenista_user, administrador_user, auxiliar_user, db):
    """Solo el Almacenista puede crear/desactivar proveedores; Administrador solo lectura; Auxiliar bloqueado."""
    # Clientes independientes para evitar que force_authenticate compartido se pise
    alma = APIClient()
    alma.force_authenticate(user=almacenista_user)
    admin = APIClient()
    admin.force_authenticate(user=administrador_user)
    aux = APIClient()
    aux.force_authenticate(user=auxiliar_user)

    supplier = _create_supplier_via_api(alma, nit="700999888-1")

    # Administrador puede leer
    r_read = admin.get(reverse("supplier-detail", kwargs={"pk": supplier["id"]}))
    assert r_read.status_code == status.HTTP_200_OK

    # Administrador NO puede crear
    r_admin_create = admin.post(
        reverse("supplier-list-create"),
        _supplier_payload(nit="700777666-2"),
        format="json",
    )
    assert r_admin_create.status_code == status.HTTP_403_FORBIDDEN

    # Auxiliar NO puede acceder al módulo
    r_aux = aux.get(reverse("supplier-list-create"))
    assert r_aux.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# RF-020 — Ciclo de vida de Órdenes de Compra
# ---------------------------------------------------------------------------


def impl_rf020_s01(authenticated_almacenista_client: APIClient, sample_product, db):
    """Creación de OC en estado BORRADOR con número secuencial OC-XXXX."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="111222333-0"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=5,
        unit_cost="20000.0000",
    )
    assert po["status"] == PurchaseOrderStatus.BORRADOR
    assert po["number"].startswith("OC-")
    assert len(po["items"]) == 1
    assert po["items"][0]["quantity_ordered"] == 5
    assert AuditLog.objects.filter(
        event_type=AuditEventType.PURCHASE_ORDER_CREATED
    ).exists()


def impl_rf020_s02(authenticated_almacenista_client: APIClient, sample_product, db):
    """Confirmación de OC: BORRADOR → PENDIENTE — queda inmutable para edición."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="222333444-1"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client, supplier["id"], str(sample_product.id)
    )
    confirmed = _confirm_po(authenticated_almacenista_client, po["id"])
    assert confirmed["status"] == PurchaseOrderStatus.PENDIENTE
    assert confirmed["confirmed_at"] is not None

    # OC confirmada no se puede editar
    r_edit = authenticated_almacenista_client.patch(
        reverse("po-detail", kwargs={"pk": po["id"]}),
        {"notes": "modificación tardía"},
        format="json",
    )
    assert r_edit.status_code in (
        status.HTTP_405_METHOD_NOT_ALLOWED,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
    assert AuditLog.objects.filter(
        event_type=AuditEventType.PURCHASE_ORDER_CONFIRMED
    ).exists()


def impl_rf020_s03(authenticated_almacenista_client: APIClient, sample_product, db):
    """Cancelación de OC sin recepciones confirmadas — BR-020."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="333444555-2"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client, supplier["id"], str(sample_product.id)
    )
    _confirm_po(authenticated_almacenista_client, po["id"])

    r = authenticated_almacenista_client.post(
        reverse("po-cancel", kwargs={"pk": po["id"]}),
        {"reason": "Proveedor no disponible en la fecha acordada"},
        format="json",
    )
    assert r.status_code == status.HTTP_200_OK
    assert r.data["status"] == PurchaseOrderStatus.CANCELADA
    assert r.data["cancellation_reason"] != ""
    assert AuditLog.objects.filter(
        event_type=AuditEventType.PURCHASE_ORDER_CANCELLED
    ).exists()


def impl_rf020_s04(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Intento de cancelar OC con recepción confirmada — BR-020 bloquea."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="444555666-3"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=10,
    )
    poi_id = po["items"][0]["id"]
    _confirm_po(authenticated_almacenista_client, po["id"])

    loc = sample_locations[0]
    reception = _create_reception_via_api(
        authenticated_almacenista_client,
        po["id"],
        poi_id,
        str(loc.id),
        quantity=10,
    )
    _confirm_reception(authenticated_almacenista_client, reception["id"])

    r = authenticated_almacenista_client.post(
        reverse("po-cancel", kwargs={"pk": po["id"]}),
        {"reason": "Intento de cancelación con stock recibido"},
        format="json",
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    from apps.purchasing.models import PurchaseOrder

    po_db = PurchaseOrder.objects.get(pk=po["id"])
    assert po_db.status != PurchaseOrderStatus.CANCELADA


def impl_rf020_s05(authenticated_almacenista_client: APIClient, sample_product, db):
    """Cancelación sin razón explícita es rechazada."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="555666777-4"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client, supplier["id"], str(sample_product.id)
    )
    _confirm_po(authenticated_almacenista_client, po["id"])

    # Sin campo reason
    r_no_reason = authenticated_almacenista_client.post(
        reverse("po-cancel", kwargs={"pk": po["id"]}),
        {},
        format="json",
    )
    assert r_no_reason.status_code in (
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    )

    # Con reason vacío
    r_empty = authenticated_almacenista_client.post(
        reverse("po-cancel", kwargs={"pk": po["id"]}),
        {"reason": "   "},
        format="json",
    )
    assert r_empty.status_code in (
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    )

    from apps.purchasing.models import PurchaseOrder

    assert (
        PurchaseOrder.objects.get(pk=po["id"]).status != PurchaseOrderStatus.CANCELADA
    )


# ---------------------------------------------------------------------------
# RF-021 — Recepciones: validaciones de entrada
# ---------------------------------------------------------------------------


def impl_rf021_s01(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Recepción parcial: solo se recibe parte de la cantidad ordenada."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="666777888-5"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=10,
    )
    poi_id = po["items"][0]["id"]
    _confirm_po(authenticated_almacenista_client, po["id"])

    loc = sample_locations[0]
    # Recibir 4 de 10 con nota de discrepancia
    reception = _create_reception_via_api(
        authenticated_almacenista_client,
        po["id"],
        poi_id,
        str(loc.id),
        quantity=4,
        discrepancy_note="Solo llegaron 4 unidades del pedido de 10.",
    )
    assert reception["status"] == ReceptionStatus.BORRADOR

    confirmed = _confirm_reception(authenticated_almacenista_client, reception["id"])
    assert confirmed["status"] == ReceptionStatus.CONFIRMADA

    # OC debe quedar PARCIALMENTE_RECIBIDA
    r_po = authenticated_almacenista_client.get(
        reverse("po-detail", kwargs={"pk": po["id"]})
    )
    assert r_po.data["status"] == PurchaseOrderStatus.PARCIALMENTE_RECIBIDA


def impl_rf021_s02(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Recepción que supera la cantidad pendiente es rechazada."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="777888999-6"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=5,
    )
    poi_id = po["items"][0]["id"]
    _confirm_po(authenticated_almacenista_client, po["id"])

    loc = sample_locations[0]
    payload = {
        "po_id": po["id"],
        "destination_location_id": str(loc.id),
        "items": [
            {
                "purchase_order_item_id": poi_id,
                "quantity_received": 99,  # supera los 5 ordenados
            }
        ],
    }
    r = authenticated_almacenista_client.post(
        reverse("reception-list-create"), payload, format="json"
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def impl_rf021_s03(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """No se puede crear recepción para una OC en BORRADOR — BR-019."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="888999000-7"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client, supplier["id"], str(sample_product.id)
    )
    # OC sigue en BORRADOR — no confirmada
    poi_id = po["items"][0]["id"]
    loc = sample_locations[0]
    payload = {
        "po_id": po["id"],
        "destination_location_id": str(loc.id),
        "items": [{"purchase_order_item_id": poi_id, "quantity_received": 3}],
    }
    r = authenticated_almacenista_client.post(
        reverse("reception-list-create"), payload, format="json"
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ---------------------------------------------------------------------------
# RF-022 — Confirmación de recepción y efecto en inventario
# ---------------------------------------------------------------------------


def impl_rf022_s01(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Confirmación genera Movements de ENTRADA y actualiza stock — BR-021."""
    from apps.inventory.models import StockByLocation
    from apps.movements.models import Movement, MovementType

    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="100200300-0"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=8,
        unit_cost="12000.0000",
    )
    poi_id = po["items"][0]["id"]
    _confirm_po(authenticated_almacenista_client, po["id"])

    loc = sample_locations[0]
    stock_before = StockByLocation.objects.filter(
        product=sample_product, location=loc
    ).first()
    qty_before = stock_before.current_stock if stock_before else 0

    reception = _create_reception_via_api(
        authenticated_almacenista_client,
        po["id"],
        poi_id,
        str(loc.id),
        quantity=8,
    )
    _confirm_reception(authenticated_almacenista_client, reception["id"])

    # El stock aumentó
    stock_after = StockByLocation.objects.get(product=sample_product, location=loc)
    assert stock_after.current_stock == qty_before + 8

    # El Movement de ENTRADA existe y tiene el costo congelado de la OC — BR-021
    movement = Movement.objects.filter(
        product=sample_product,
        destination_location=loc,
        movement_type=MovementType.ENTRADA,
    ).latest("created_at")
    assert movement.unit_cost == Decimal("12000.0000")

    # El ReceptionItem enlaza al Movement
    from apps.purchasing.models import ReceptionItem

    ri = ReceptionItem.objects.get(reception_id=reception["id"])
    assert ri.movement == movement

    assert AuditLog.objects.filter(
        event_type=AuditEventType.RECEPTION_CONFIRMED
    ).exists()


def impl_rf022_s02(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Recepción completa marca la OC como COMPLETADA."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="200300400-1"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=6,
    )
    poi_id = po["items"][0]["id"]
    _confirm_po(authenticated_almacenista_client, po["id"])

    loc = sample_locations[0]
    reception = _create_reception_via_api(
        authenticated_almacenista_client,
        po["id"],
        poi_id,
        str(loc.id),
        quantity=6,  # exactamente lo ordenado
    )
    _confirm_reception(authenticated_almacenista_client, reception["id"])

    r_po = authenticated_almacenista_client.get(
        reverse("po-detail", kwargs={"pk": po["id"]})
    )
    assert r_po.data["status"] == PurchaseOrderStatus.COMPLETADA


def impl_rf022_s03(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Recepción parcial marca la OC como PARCIALMENTE_RECIBIDA."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="300400500-2"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=10,
    )
    poi_id = po["items"][0]["id"]
    _confirm_po(authenticated_almacenista_client, po["id"])

    loc = sample_locations[0]
    reception = _create_reception_via_api(
        authenticated_almacenista_client,
        po["id"],
        poi_id,
        str(loc.id),
        quantity=3,
        discrepancy_note="Llegaron 3 de 10 en el primer envío.",
    )
    _confirm_reception(authenticated_almacenista_client, reception["id"])

    r_po = authenticated_almacenista_client.get(
        reverse("po-detail", kwargs={"pk": po["id"]})
    )
    assert r_po.data["status"] == PurchaseOrderStatus.PARCIALMENTE_RECIBIDA


def impl_rf022_s04(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Error al confirmar recepción vacía (sin ítems activos) revierte la operación."""
    from apps.purchasing.models import Reception

    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="400500600-3"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=5,
    )
    poi_id = po["items"][0]["id"]
    _confirm_po(authenticated_almacenista_client, po["id"])

    loc = sample_locations[0]
    # Crear recepción con cantidad 0 (vacía)
    payload = {
        "po_id": po["id"],
        "destination_location_id": str(loc.id),
        "items": [{"purchase_order_item_id": poi_id, "quantity_received": 0}],
    }
    r_create = authenticated_almacenista_client.post(
        reverse("reception-list-create"), payload, format="json"
    )
    assert r_create.status_code == status.HTTP_201_CREATED
    reception_id = r_create.data["id"]

    # Confirmar debe fallar: recepción vacía
    r_confirm = authenticated_almacenista_client.post(
        reverse("reception-confirm", kwargs={"pk": reception_id})
    )
    assert r_confirm.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # La recepción sigue en BORRADOR — no hubo efecto en inventario
    rec = Reception.objects.get(pk=reception_id)
    assert rec.status == ReceptionStatus.BORRADOR


def impl_rf022_s05(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Discrepancia sin nota es rechazada al confirmar — BR-009 aplicado a compras."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="500600700-4"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=10,
    )
    poi_id = po["items"][0]["id"]
    _confirm_po(authenticated_almacenista_client, po["id"])

    loc = sample_locations[0]
    # Crear recepción con discrepancia pero SIN nota
    payload = {
        "po_id": po["id"],
        "destination_location_id": str(loc.id),
        "items": [
            {
                "purchase_order_item_id": poi_id,
                "quantity_received": 7,  # difiere de 10 → discrepancia
                "discrepancy_note": "",  # sin nota → debe fallar al confirmar
            }
        ],
    }
    r_create = authenticated_almacenista_client.post(
        reverse("reception-list-create"), payload, format="json"
    )
    assert r_create.status_code == status.HTTP_201_CREATED

    r_confirm = authenticated_almacenista_client.post(
        reverse("reception-confirm", kwargs={"pk": r_create.data["id"]})
    )
    assert r_confirm.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def impl_rf021_s04(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Recepción avanzada por lote y ubicación se crea correctamente."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="555666888-5"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=10,
    )
    poi_id = po["items"][0]["id"]
    _confirm_po(authenticated_almacenista_client, po["id"])

    loc_a = sample_locations[0]
    loc_b = sample_locations[1]
    reception = authenticated_almacenista_client.post(
        reverse("reception-list-create"),
        {
            "po_id": po["id"],
            "destination_location_id": str(loc_a.id),
            "items": [
                {
                    "purchase_order_item_id": poi_id,
                    "quantity_received": 10,
                    "allocations": [
                        {
                            "location_id": str(loc_a.id),
                            "quantity_received": 4,
                            "lot_code": "LOTE-A",
                            "lot_expiration_date": "2027-12-31",
                        },
                        {
                            "location_id": str(loc_b.id),
                            "quantity_received": 6,
                            "lot_code": "LOTE-B",
                            "lot_expiration_date": "2028-01-31",
                        },
                    ],
                }
            ],
        },
        format="json",
    )
    assert reception.status_code == status.HTTP_201_CREATED, reception.data
    assert reception.data["status"] == ReceptionStatus.BORRADOR
    assert len(reception.data["items"]) == 1
    assert len(reception.data["items"][0]["allocations"]) == 2

    r_po = authenticated_almacenista_client.get(
        reverse("po-detail", kwargs={"pk": po["id"]})
    )
    assert r_po.data["status"] == PurchaseOrderStatus.PENDIENTE


def impl_rf021_s05(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Recepción avanzada rechaza distribuciones cuya suma no coincide."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="666777999-6"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=10,
    )
    poi_id = po["items"][0]["id"]
    _confirm_po(authenticated_almacenista_client, po["id"])

    loc_a = sample_locations[0]
    loc_b = sample_locations[1]
    response = authenticated_almacenista_client.post(
        reverse("reception-list-create"),
        {
            "po_id": po["id"],
            "destination_location_id": str(loc_a.id),
            "items": [
                {
                    "purchase_order_item_id": poi_id,
                    "quantity_received": 10,
                    "allocations": [
                        {
                            "location_id": str(loc_a.id),
                            "quantity_received": 4,
                        },
                        {
                            "location_id": str(loc_b.id),
                            "quantity_received": 5,
                        },
                    ],
                }
            ],
        },
        format="json",
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def impl_rf022_s06(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Confirmación de recepción avanzada genera un Movement por porción."""
    from apps.inventory.models import StockByLocation
    from apps.movements.models import Movement, MovementType
    from apps.purchasing.models import ReceptionItem

    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="777888000-7"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=10,
    )
    poi_id = po["items"][0]["id"]
    _confirm_po(authenticated_almacenista_client, po["id"])

    loc_a = sample_locations[0]
    loc_b = sample_locations[1]
    reception = authenticated_almacenista_client.post(
        reverse("reception-list-create"),
        {
            "po_id": po["id"],
            "destination_location_id": str(loc_a.id),
            "items": [
                {
                    "purchase_order_item_id": poi_id,
                    "quantity_received": 10,
                    "allocations": [
                        {
                            "location_id": str(loc_a.id),
                            "quantity_received": 4,
                            "lot_code": "LOTE-A",
                            "lot_expiration_date": "2027-12-31",
                        },
                        {
                            "location_id": str(loc_b.id),
                            "quantity_received": 6,
                            "lot_code": "LOTE-B",
                            "lot_expiration_date": "2028-01-31",
                        },
                    ],
                }
            ],
        },
        format="json",
    )
    assert reception.status_code == status.HTTP_201_CREATED, reception.data

    confirmed = _confirm_reception(
        authenticated_almacenista_client, reception.data["id"]
    )
    assert confirmed["status"] == ReceptionStatus.CONFIRMADA

    movements = Movement.objects.filter(
        product=sample_product,
        movement_type=MovementType.ENTRADA,
    ).order_by("created_at")
    assert movements.count() == 2

    assert (
        StockByLocation.objects.get(
            product=sample_product, location=loc_a
        ).current_stock
        == 4
    )
    assert (
        StockByLocation.objects.get(
            product=sample_product, location=loc_b
        ).current_stock
        == 6
    )

    ri = ReceptionItem.objects.get(reception_id=reception.data["id"])
    assert ri.allocations.count() == 2
    assert ri.allocations.filter(movement__isnull=False).count() == 2
    assert AuditLog.objects.filter(
        event_type=AuditEventType.RECEPTION_CONFIRMED
    ).exists()


def impl_rf022_s07(
    almacenista_user,
    authenticated_almacenista_client: APIClient,
    sample_product,
    sample_locations,
    db,
):
    """Confirmación de recepción avanzada con suma inconsistente es rechazada."""
    from apps.inventory.models import StockByLocation
    from apps.purchasing.models import (
        PurchaseOrder,
        PurchaseOrderItem,
        Reception,
        ReceptionItem,
        ReceptionItemAllocation,
        ReceptionStatus,
    )

    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="888999111-8"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=10,
    )
    poi_id = po["items"][0]["id"]
    _confirm_po(authenticated_almacenista_client, po["id"])

    loc_a = sample_locations[0]
    loc_b = sample_locations[1]
    po_db = PurchaseOrder.objects.get(pk=po["id"])
    poi_db = PurchaseOrderItem.objects.get(pk=poi_id)
    reception = Reception.objects.create(
        purchase_order=po_db,
        destination_location=loc_a,
        received_by=almacenista_user,
        status=ReceptionStatus.BORRADOR,
    )
    item = ReceptionItem.objects.create(
        reception=reception,
        purchase_order_item=poi_db,
        quantity_received=10,
        discrepancy_note="Distribución cargada manualmente para validar rechazo en confirmación.",
    )
    ReceptionItemAllocation.objects.create(
        reception_item=item,
        location=loc_a,
        quantity_received=4,
    )
    ReceptionItemAllocation.objects.create(
        reception_item=item,
        location=loc_b,
        quantity_received=5,
    )

    response = authenticated_almacenista_client.post(
        reverse("reception-confirm", kwargs={"pk": reception.id})
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    rec = Reception.objects.get(pk=reception.id)
    assert rec.status == ReceptionStatus.BORRADOR
    assert not StockByLocation.objects.filter(
        product=sample_product, location=loc_a
    ).exists()
    assert not StockByLocation.objects.filter(
        product=sample_product, location=loc_b
    ).exists()


# ---------------------------------------------------------------------------
# RF-023 — Cancelación de recepciones
# ---------------------------------------------------------------------------


def impl_rf023_s01(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Cancelación exitosa de recepción en BORRADOR — sin efecto en inventario."""
    from apps.inventory.models import StockByLocation

    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="600700800-5"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=5,
    )
    poi_id = po["items"][0]["id"]
    _confirm_po(authenticated_almacenista_client, po["id"])

    loc = sample_locations[0]
    reception = _create_reception_via_api(
        authenticated_almacenista_client,
        po["id"],
        poi_id,
        str(loc.id),
        quantity=5,
    )

    stock_before = StockByLocation.objects.filter(
        product=sample_product, location=loc
    ).first()
    qty_before = stock_before.current_stock if stock_before else 0

    r = authenticated_almacenista_client.post(
        reverse("reception-cancel", kwargs={"pk": reception["id"]})
    )
    assert r.status_code == status.HTTP_200_OK
    assert r.data["status"] == ReceptionStatus.CANCELADA

    # Stock no cambió
    stock_after = StockByLocation.objects.filter(
        product=sample_product, location=loc
    ).first()
    qty_after = stock_after.current_stock if stock_after else 0
    assert qty_after == qty_before

    assert AuditLog.objects.filter(
        event_type=AuditEventType.RECEPTION_CANCELLED
    ).exists()


def impl_rf023_s02(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """No se puede cancelar una recepción CONFIRMADA."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="700800900-6"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=5,
    )
    poi_id = po["items"][0]["id"]
    _confirm_po(authenticated_almacenista_client, po["id"])

    loc = sample_locations[0]
    reception = _create_reception_via_api(
        authenticated_almacenista_client,
        po["id"],
        poi_id,
        str(loc.id),
        quantity=5,
    )
    _confirm_reception(authenticated_almacenista_client, reception["id"])

    r = authenticated_almacenista_client.post(
        reverse("reception-cancel", kwargs={"pk": reception["id"]})
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    from apps.purchasing.models import Reception

    assert (
        Reception.objects.get(pk=reception["id"]).status == ReceptionStatus.CONFIRMADA
    )


# ---------------------------------------------------------------------------
# RF-024 — Trazabilidad OC ↔ Movement ↔ Auditoría
# ---------------------------------------------------------------------------


def impl_rf024_s01(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Desde un Movement de ENTRADA se puede trazar la OC de origen."""
    from apps.movements.models import Movement, MovementType
    from apps.purchasing.models import ReceptionItem

    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="800900001-7"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=4,
        unit_cost="18000.0000",
    )
    poi_id = po["items"][0]["id"]
    _confirm_po(authenticated_almacenista_client, po["id"])

    loc = sample_locations[0]
    reception = _create_reception_via_api(
        authenticated_almacenista_client,
        po["id"],
        poi_id,
        str(loc.id),
        quantity=4,
    )
    _confirm_reception(authenticated_almacenista_client, reception["id"])

    # El Movement tiene un ReceptionItem enlazado → de ahí se llega a la OC
    movement = Movement.objects.filter(
        product=sample_product,
        movement_type=MovementType.ENTRADA,
    ).latest("created_at")

    ri = ReceptionItem.objects.get(movement=movement)
    po_linked = ri.reception.purchase_order
    assert str(po_linked.id) == po["id"]

    # El costo unitario en el Movement coincide con el de la OC — BR-021
    assert movement.unit_cost == Decimal("18000.0000")


def impl_rf024_s02(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """El log de auditoría registra todos los eventos del ciclo completo de una OC."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="900001002-8"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=3,
    )
    poi_id = po["items"][0]["id"]
    _confirm_po(authenticated_almacenista_client, po["id"])

    loc = sample_locations[0]
    reception = _create_reception_via_api(
        authenticated_almacenista_client,
        po["id"],
        poi_id,
        str(loc.id),
        quantity=3,
    )
    _confirm_reception(authenticated_almacenista_client, reception["id"])

    expected_events = [
        AuditEventType.SUPPLIER_CREATED,
        AuditEventType.PURCHASE_ORDER_CREATED,
        AuditEventType.PURCHASE_ORDER_CONFIRMED,
        AuditEventType.RECEPTION_CREATED,
        AuditEventType.RECEPTION_CONFIRMED,
    ]
    for event in expected_events:
        assert AuditLog.objects.filter(event_type=event).exists(), (
            f"Evento esperado en audit log no encontrado: {event}"
        )


# ---------------------------------------------------------------------------
# RF-025 — Control de acceso por rol al módulo de compras
# ---------------------------------------------------------------------------


def impl_rf025_s01(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Almacenista tiene acceso completo: crear proveedor, OC, recepción y confirmar."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="001002003-9"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client,
        supplier["id"],
        str(sample_product.id),
        quantity_ordered=2,
    )
    poi_id = po["items"][0]["id"]
    _confirm_po(authenticated_almacenista_client, po["id"])

    loc = sample_locations[0]
    reception = _create_reception_via_api(
        authenticated_almacenista_client, po["id"], poi_id, str(loc.id), quantity=2
    )
    confirmed = _confirm_reception(authenticated_almacenista_client, reception["id"])
    assert confirmed["status"] == ReceptionStatus.CONFIRMADA


def impl_rf025_s02(almacenista_user, administrador_user, sample_product, db):
    """Administrador tiene acceso de solo lectura al módulo de compras."""
    # Clientes independientes para evitar pisada de force_authenticate
    alma = APIClient()
    alma.force_authenticate(user=almacenista_user)
    admin = APIClient()
    admin.force_authenticate(user=administrador_user)

    supplier = _create_supplier_via_api(alma, nit="002003004-0")
    po = _create_po_via_api(alma, supplier["id"], str(sample_product.id))

    # Administrador puede leer proveedores y OC
    r_suppliers = admin.get(reverse("supplier-list-create"))
    assert r_suppliers.status_code == status.HTTP_200_OK

    r_po = admin.get(reverse("po-detail", kwargs={"pk": po["id"]}))
    assert r_po.status_code == status.HTTP_200_OK

    # Administrador NO puede crear un proveedor
    r_create = admin.post(
        reverse("supplier-list-create"),
        _supplier_payload(nit="999888777-5"),
        format="json",
    )
    assert r_create.status_code == status.HTTP_403_FORBIDDEN

    # Administrador NO puede confirmar una OC
    r_confirm = admin.post(reverse("po-confirm", kwargs={"pk": po["id"]}))
    assert r_confirm.status_code == status.HTTP_403_FORBIDDEN


def impl_rf025_s03(
    api_client: APIClient,
    auxiliar_user,
    authenticated_almacenista_client: APIClient,
    sample_product,
    db,
):
    """Auxiliar de Despacho no tiene acceso al módulo de compras."""
    supplier = _create_supplier_via_api(
        authenticated_almacenista_client, nit="003004005-1"
    )
    po = _create_po_via_api(
        authenticated_almacenista_client, supplier["id"], str(sample_product.id)
    )

    api_client.force_authenticate(user=auxiliar_user)

    r_suppliers = api_client.get(reverse("supplier-list-create"))
    assert r_suppliers.status_code == status.HTTP_403_FORBIDDEN

    r_po_list = api_client.get(reverse("po-list-create"))
    assert r_po_list.status_code == status.HTTP_403_FORBIDDEN

    r_receptions = api_client.get(reverse("reception-list-create"))
    assert r_receptions.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------

IMPLEMENTATIONS: dict[str, object] = {
    "RF019-S01": impl_rf019_s01,
    "RF019-S02": impl_rf019_s02,
    "RF019-S03": impl_rf019_s03,
    "RF019-S04": impl_rf019_s04,
    "RF020-S01": impl_rf020_s01,
    "RF020-S02": impl_rf020_s02,
    "RF020-S03": impl_rf020_s03,
    "RF020-S04": impl_rf020_s04,
    "RF020-S05": impl_rf020_s05,
    "RF021-S01": impl_rf021_s01,
    "RF021-S02": impl_rf021_s02,
    "RF021-S03": impl_rf021_s03,
    "RF021-S04": impl_rf021_s04,
    "RF021-S05": impl_rf021_s05,
    "RF022-S01": impl_rf022_s01,
    "RF022-S02": impl_rf022_s02,
    "RF022-S03": impl_rf022_s03,
    "RF022-S04": impl_rf022_s04,
    "RF022-S05": impl_rf022_s05,
    "RF022-S06": impl_rf022_s06,
    "RF022-S07": impl_rf022_s07,
    "RF023-S01": impl_rf023_s01,
    "RF023-S02": impl_rf023_s02,
    "RF024-S01": impl_rf024_s01,
    "RF024-S02": impl_rf024_s02,
    "RF025-S01": impl_rf025_s01,
    "RF025-S02": impl_rf025_s02,
    "RF025-S03": impl_rf025_s03,
}
