"""Vistas de inventario (RF-004)."""

from __future__ import annotations

from uuid import UUID

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.inventory.models import Location, StockByLocation
from apps.inventory.selectors import (
    get_full_inventory,
    get_stock_by_location,
    get_stock_by_product,
    search_products,
)
from apps.inventory.serializers import (
    LocationCreateSerializer,
    LocationSerializer,
    LocationStateTransitionSerializer,
    PaginatedProductListSerializer,
    PaginatedStockByLocationListSerializer,
    ProductSerializer,
    StockByLocationSerializer,
    StockByProductResponseSerializer,
    StockReconstructRequestSerializer,
    StockReconstructResponseSerializer,
    StockThresholdSerializer,
    StorageTemplateCreateSerializer,
    StorageTemplateSerializer,
    StorageTypeCreateSerializer,
    StorageTypeSerializer,
)
from apps.inventory.services import (
    create_location,
    create_storage_template,
    create_storage_type,
    disable_storage_template,
    disable_storage_type,
    enable_storage_template,
    enable_storage_type,
    restore_location,
    restore_storage_template,
    restore_storage_type,
    soft_delete_location,
    soft_delete_storage_template,
    soft_delete_storage_type,
    transition_location_state,
    trigger_stock_reconstruction,
    update_location,
    update_storage_template,
    update_storage_type,
)
from shared.exporters import export_to_csv, export_to_xlsx
from shared.openapi import TAG_INVENTORY, standard_error_responses
from shared.pagination import ICMPageNumberPagination
from shared.permissions import IsAlmacenista

_INVENTORY_EXPORT_HEADERS = [
    "sku",
    "name",
    "reorder_point",
    "total",
    "location_code",
    "location_name",
    "quantity",
]


class InventoryFullListView(APIView):
    """GET — Inventario consolidado por producto (RF-004)."""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Inventario consolidado",
        description="Devuelve el inventario consolidado por producto con filtros y exportación.",
        parameters=[
            OpenApiParameter(
                name="category_id",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="location_id",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="storage_type_id",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filtra productos con stock en ubicaciones del tipo dado.",
            ),
            OpenApiParameter(
                name="operational_status",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filtra productos con stock en ubicaciones con este estado operativo.",
            ),
            OpenApiParameter(
                name="only_in_stock",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="stock_below_reorder",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(description="Inventario listado exitosamente."),
            **standard_error_responses(),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request):
        filters: dict = {}
        if cid := request.query_params.get("category_id"):
            try:
                filters["category_id"] = UUID(str(cid))
            except (ValueError, AttributeError):
                raise ValidationError({"category_id": "UUID inválido."})
        if lid := request.query_params.get("location_id"):
            try:
                filters["location_id"] = UUID(str(lid))
            except (ValueError, AttributeError):
                raise ValidationError({"location_id": "UUID inválido."})
        if stid := request.query_params.get("storage_type_id"):
            try:
                filters["storage_type_id"] = UUID(str(stid))
            except (ValueError, AttributeError):
                raise ValidationError({"storage_type_id": "UUID inválido."})
        if os_val := request.query_params.get("operational_status"):
            filters["operational_status"] = str(os_val)
        if request.query_params.get("only_in_stock", "").lower() in (
            "1",
            "true",
            "yes",
        ):
            filters["only_in_stock"] = True
        if request.query_params.get("stock_below_reorder", "").lower() in (
            "1",
            "true",
            "yes",
        ):
            filters["stock_below_reorder"] = True
        data = get_full_inventory(filters)

        export = request.query_params.get("export", "").lower()
        if export in ("csv", "xlsx"):
            log_event(
                AuditEventType.REPORT_GENERATED,
                user=request.user,
                detail={
                    "kind": "inventory-full",
                    "format": export,
                    "_origin": "API",
                },
            )
            # Aplanar estructura anidada producto→ubicación a una fila por registro
            rows = [
                {
                    "sku": item["sku"],
                    "name": item["name"],
                    "reorder_point": item["reorder_point"],
                    "total": item["total"],
                    "location_code": loc["location_code"],
                    "location_name": loc["location_name"],
                    "quantity": loc["quantity"],
                }
                for item in data
                for loc in item.get(
                    "by_location",
                    [
                        {
                            "location_code": "",
                            "location_name": "",
                            "quantity": item["total"],
                        }
                    ],
                )
            ]
            if export == "csv":
                return export_to_csv(_INVENTORY_EXPORT_HEADERS, rows, "inventory.csv")
            return export_to_xlsx(_INVENTORY_EXPORT_HEADERS, rows, "inventory.xlsx")

        paginator = ICMPageNumberPagination()
        page = paginator.paginate_queryset(data, request, view=self)
        return paginator.get_paginated_response(page)


class LocationListCreateView(APIView):
    """GET/POST ubicaciones (RF-004)."""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAlmacenista()]
        return [IsAuthenticated()]

    @extend_schema(
        summary="Listar ubicaciones",
        description="Lista las ubicaciones registradas (excluye eliminadas lógicamente por defecto).",
        parameters=[
            OpenApiParameter(
                name="include_archived",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Si es true, incluye ubicaciones eliminadas lógicamente (deleted_at != null).",
            ),
            OpenApiParameter(
                name="include_inactive",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Si es true, incluye ubicaciones con operational_status distinto de ACTIVE.",
            ),
        ],
        responses={
            200: LocationSerializer(many=True),
            **standard_error_responses(),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request):
        include_archived = request.query_params.get("include_archived", "").lower() in (
            "1",
            "true",
            "yes",
        )
        qs = Location.objects.order_by("code")
        if not include_archived:
            qs = qs.filter(deleted_at__isnull=True)
        include_inactive = request.query_params.get("include_inactive", "").lower()
        if include_inactive not in ("1", "true", "yes"):
            qs = qs.filter(operational_status=Location.OperationalStatus.ACTIVE)
        paginator = ICMPageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            return paginator.get_paginated_response(
                LocationSerializer(page, many=True).data
            )
        return Response(LocationSerializer(qs, many=True).data)

    @extend_schema(
        summary="Crear ubicación",
        description="Crea una nueva ubicación de inventario.",
        request=LocationCreateSerializer,
        responses={
            201: LocationSerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_INVENTORY],
    )
    def post(self, request):
        ser = LocationCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        loc = create_location(
            request.user,
            name=d["name"],
            description=d.get("description", ""),
            is_retail=d.get("is_retail", None),
            max_capacity=d.get("max_capacity", None),
            storage_type_id=d.get("storage_type_id"),
            storage_template_id=d.get("storage_template_id"),
            operational_status=d.get(
                "operational_status", Location.OperationalStatus.ACTIVE
            ),
            capacity_mode=d.get("capacity_mode", Location.CapacityMode.NONE),
            capacity_level=d.get("capacity_level"),
            capacity_score=d.get("capacity_score"),
            occupancy_estimate_pct=d.get("occupancy_estimate_pct"),
        )
        return Response(LocationSerializer(loc).data, status=status.HTTP_201_CREATED)


class StorageTemplateListCreateView(APIView):
    """GET/POST plantillas de almacenamiento."""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAlmacenista()]
        return [IsAuthenticated()]

    @extend_schema(
        summary="Listar plantillas de almacenamiento",
        description="Lista las plantillas de almacenamiento registradas (excluye eliminadas lógicamente por defecto).",
        parameters=[
            OpenApiParameter(
                name="include_archived",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Si es true, incluye plantillas eliminadas lógicamente (deleted_at != null).",
            ),
            OpenApiParameter(
                name="is_active",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filtra por disponibilidad (is_active=true/false).",
            ),
        ],
        responses={
            200: StorageTemplateSerializer(many=True),
            **standard_error_responses(),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request):
        from apps.inventory.models import StorageTemplate

        include_archived = request.query_params.get("include_archived", "").lower() in (
            "1",
            "true",
            "yes",
        )
        qs = StorageTemplate.objects.select_related("storage_type")
        if not include_archived:
            qs = qs.filter(deleted_at__isnull=True)
        is_active_param = request.query_params.get("is_active")
        if is_active_param is not None:
            qs = qs.filter(is_active=is_active_param.lower() in ("true", "1", "yes"))
        data = StorageTemplateSerializer(
            qs.order_by("sort_order", "name"), many=True
        ).data
        return Response(data)

    @extend_schema(
        summary="Crear plantilla de almacenamiento",
        description="Crea una nueva plantilla de almacenamiento.",
        request=StorageTemplateCreateSerializer,
        responses={
            201: StorageTemplateSerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_INVENTORY],
    )
    def post(self, request):
        ser = StorageTemplateCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        template = create_storage_template(request.user, **ser.validated_data)
        return Response(
            StorageTemplateSerializer(template).data,
            status=status.HTTP_201_CREATED,
        )


class StorageTemplateDetailView(APIView):
    """GET/PATCH/DELETE(soft) plantilla de almacenamiento por id."""

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAlmacenista()]

    @extend_schema(
        summary="Detalle de plantilla de almacenamiento",
        description="Obtiene el detalle de una plantilla de almacenamiento.",
        responses={
            200: StorageTemplateSerializer,
            **standard_error_responses(include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request, pk):
        from apps.inventory.models import StorageTemplate

        template = get_object_or_404(StorageTemplate, pk=pk)
        return Response(StorageTemplateSerializer(template).data)

    @extend_schema(
        summary="Reemplazar plantilla de almacenamiento",
        description="Reemplaza completamente los datos de una plantilla de almacenamiento.",
        request=StorageTemplateCreateSerializer,
        responses={
            200: StorageTemplateSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def put(self, request, pk):
        from apps.inventory.models import StorageTemplate

        get_object_or_404(StorageTemplate, pk=pk)
        ser = StorageTemplateCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        template = update_storage_template(
            request.user, UUID(str(pk)), ser.validated_data
        )
        return Response(StorageTemplateSerializer(template).data)

    @extend_schema(
        summary="Actualizar plantilla de almacenamiento",
        description="Actualiza parcialmente una plantilla de almacenamiento.",
        request=StorageTemplateCreateSerializer,
        responses={
            200: StorageTemplateSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def patch(self, request, pk):
        ser = StorageTemplateCreateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        template = update_storage_template(
            request.user, UUID(str(pk)), ser.validated_data
        )
        return Response(StorageTemplateSerializer(template).data)

    @extend_schema(
        summary="Eliminar lógicamente plantilla de almacenamiento (soft delete)",
        description=(
            "Marca la plantilla como eliminada lógicamente (deleted_at=now). "
            "Deja de estar disponible para asignación y se excluye de listados por defecto. "
            "Para restaurarla use POST /storage-templates/{id}/restore/."
        ),
        responses={
            204: OpenApiResponse(
                description="Plantilla de almacenamiento eliminada lógicamente."
            ),
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def delete(self, request, pk):
        from apps.inventory.models import StorageTemplate

        get_object_or_404(StorageTemplate, pk=pk)
        soft_delete_storage_template(request.user, UUID(str(pk)), request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class StorageTemplateRestoreView(APIView):
    """POST — Restaura una plantilla de almacenamiento previamente eliminada lógicamente."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Restaurar plantilla de almacenamiento",
        description="Restaura una plantilla de almacenamiento previamente eliminada lógicamente.",
        tags=[TAG_INVENTORY],
        responses={
            200: StorageTemplateSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        from apps.inventory.models import StorageTemplate

        get_object_or_404(StorageTemplate, pk=pk)
        template = restore_storage_template(
            request.user, UUID(str(pk)), request=request
        )
        return Response(StorageTemplateSerializer(template).data)


class StorageTemplateDisableView(APIView):
    """POST — Desactiva una plantilla para asignación (pausa temporal)."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Desactivar plantilla de almacenamiento",
        description=(
            "Marca la plantilla como inactiva para asignación (pausa temporal). "
            "La plantilla NO se elimina y puede reactivarse con POST /enable/."
        ),
        tags=[TAG_INVENTORY],
        responses={
            200: StorageTemplateSerializer,
            409: OpenApiResponse(
                description="Plantilla archivada; restáurela primero."
            ),
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        from apps.inventory.models import StorageTemplate

        get_object_or_404(StorageTemplate, pk=pk)
        try:
            disable_storage_template(request.user, UUID(str(pk)), request=request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        template = StorageTemplate.objects.get(pk=pk)
        return Response(StorageTemplateSerializer(template).data)


class StorageTemplateEnableView(APIView):
    """POST — Reactiva una plantilla para asignación."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Activar plantilla de almacenamiento",
        description="Reactiva una plantilla de almacenamiento previamente desactivada (pausa).",
        tags=[TAG_INVENTORY],
        responses={
            200: StorageTemplateSerializer,
            409: OpenApiResponse(
                description="Plantilla archivada; restáurela primero."
            ),
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        from apps.inventory.models import StorageTemplate

        get_object_or_404(StorageTemplate, pk=pk)
        try:
            enable_storage_template(request.user, UUID(str(pk)), request=request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        template = StorageTemplate.objects.get(pk=pk)
        return Response(StorageTemplateSerializer(template).data)


class StorageTypeListCreateView(APIView):
    """GET/POST tipos de almacenamiento."""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAlmacenista()]
        return [IsAuthenticated()]

    @extend_schema(
        summary="Listar tipos de almacenamiento",
        description="Lista los tipos de almacenamiento registrados (excluye eliminados lógicamente por defecto).",
        parameters=[
            OpenApiParameter(
                name="include_archived",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Si es true, incluye tipos eliminados lógicamente (deleted_at != null).",
            ),
            OpenApiParameter(
                name="is_active",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filtra por disponibilidad (is_active=true/false).",
            ),
        ],
        responses={
            200: StorageTypeSerializer(many=True),
            **standard_error_responses(),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request):
        from apps.inventory.models import StorageType

        include_archived = request.query_params.get("include_archived", "").lower() in (
            "1",
            "true",
            "yes",
        )
        qs = StorageType.objects.all()
        if not include_archived:
            qs = qs.filter(deleted_at__isnull=True)
        is_active_param = request.query_params.get("is_active")
        if is_active_param is not None:
            qs = qs.filter(is_active=is_active_param.lower() in ("true", "1", "yes"))
        data = StorageTypeSerializer(qs.order_by("sort_order", "name"), many=True).data
        return Response(data)

    @extend_schema(
        summary="Crear tipo de almacenamiento",
        description="Crea un nuevo tipo de almacenamiento.",
        request=StorageTypeCreateSerializer,
        responses={
            201: StorageTypeSerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_INVENTORY],
    )
    def post(self, request):
        ser = StorageTypeCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        st = create_storage_type(request.user, **ser.validated_data)
        return Response(StorageTypeSerializer(st).data, status=status.HTTP_201_CREATED)


class StorageTypeDetailView(APIView):
    """GET/PATCH/DELETE(soft) tipo de almacenamiento por id."""

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAlmacenista()]

    @extend_schema(
        summary="Detalle de tipo de almacenamiento",
        description="Obtiene el detalle de un tipo de almacenamiento.",
        responses={
            200: StorageTypeSerializer,
            **standard_error_responses(include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request, pk):
        from apps.inventory.models import StorageType

        st = get_object_or_404(StorageType, pk=pk)
        return Response(StorageTypeSerializer(st).data)

    @extend_schema(
        summary="Actualizar tipo de almacenamiento",
        description="Actualiza un tipo de almacenamiento.",
        request=StorageTypeCreateSerializer,
        responses={
            200: StorageTypeSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def put(self, request, pk):
        ser = StorageTypeCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        st = update_storage_type(request.user, UUID(str(pk)), ser.validated_data)
        return Response(StorageTypeSerializer(st).data)

    @extend_schema(
        summary="Actualizar tipo de almacenamiento parcialmente",
        description="Actualiza parcialmente un tipo de almacenamiento.",
        request=StorageTypeCreateSerializer,
        responses={
            200: StorageTypeSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def patch(self, request, pk):
        ser = StorageTypeCreateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        st = update_storage_type(request.user, UUID(str(pk)), ser.validated_data)
        return Response(StorageTypeSerializer(st).data)

    @extend_schema(
        summary="Eliminar lógicamente tipo de almacenamiento (soft delete)",
        description=(
            "Marca el tipo de almacenamiento como eliminado lógicamente (deleted_at=now). "
            "Deja de estar disponible para asignación y se excluye de listados por defecto. "
            "Para restaurarlo use POST /storage-types/{id}/restore/."
        ),
        responses={
            204: OpenApiResponse(
                description="Tipo de almacenamiento eliminado lógicamente."
            ),
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def delete(self, request, pk):
        from apps.inventory.models import StorageType

        get_object_or_404(StorageType, pk=pk)
        soft_delete_storage_type(request.user, UUID(str(pk)), request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class StorageTypeRestoreView(APIView):
    """POST — Restaura un tipo de almacenamiento previamente eliminado lógicamente."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Restaurar tipo de almacenamiento",
        description="Restaura un tipo de almacenamiento previamente eliminado lógicamente.",
        tags=[TAG_INVENTORY],
        responses={
            200: StorageTypeSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        from apps.inventory.models import StorageType

        get_object_or_404(StorageType, pk=pk)
        st = restore_storage_type(request.user, UUID(str(pk)), request=request)
        return Response(StorageTypeSerializer(st).data)


class StorageTypeDisableView(APIView):
    """POST — Desactiva un tipo de almacenamiento para asignación (pausa temporal)."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Desactivar tipo de almacenamiento",
        description=(
            "Marca el tipo de almacenamiento como inactivo para asignación (pausa temporal). "
            "El tipo NO se elimina y puede reactivarse con POST /enable/."
        ),
        tags=[TAG_INVENTORY],
        responses={
            200: StorageTypeSerializer,
            409: OpenApiResponse(description="Tipo archivado; restáurelo primero."),
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        from apps.inventory.models import StorageType

        get_object_or_404(StorageType, pk=pk)
        try:
            disable_storage_type(request.user, UUID(str(pk)), request=request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        st = StorageType.objects.get(pk=pk)
        return Response(StorageTypeSerializer(st).data)


class StorageTypeEnableView(APIView):
    """POST — Reactiva un tipo de almacenamiento para asignación."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Activar tipo de almacenamiento",
        description="Reactiva un tipo de almacenamiento previamente desactivado (pausa).",
        tags=[TAG_INVENTORY],
        responses={
            200: StorageTypeSerializer,
            409: OpenApiResponse(description="Tipo archivado; restáurelo primero."),
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        from apps.inventory.models import StorageType

        get_object_or_404(StorageType, pk=pk)
        try:
            enable_storage_type(request.user, UUID(str(pk)), request=request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        st = StorageType.objects.get(pk=pk)
        return Response(StorageTypeSerializer(st).data)


class LocationDetailView(APIView):
    """GET/PATCH/DELETE(soft) ubicación por id (RF-004)."""

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAlmacenista()]

    @extend_schema(
        summary="Detalle de ubicación",
        description="Obtiene el detalle de una ubicación.",
        responses={
            200: LocationSerializer,
            **standard_error_responses(include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request, pk):
        loc = get_object_or_404(Location, pk=pk)
        return Response(LocationSerializer(loc).data)

    @extend_schema(
        summary="Actualizar ubicación",
        description="Actualiza una ubicación.",
        request=LocationSerializer,
        responses={
            200: LocationSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def put(self, request, pk):
        ser = LocationSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        loc = update_location(request.user, UUID(str(pk)), ser.validated_data)
        return Response(LocationSerializer(loc).data)

    @extend_schema(
        summary="Actualizar ubicación parcialmente",
        description="Actualiza parcialmente una ubicación.",
        request=LocationSerializer,
        responses={
            200: LocationSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def patch(self, request, pk):
        ser = LocationSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        loc = update_location(request.user, UUID(str(pk)), ser.validated_data)
        return Response(LocationSerializer(loc).data)

    @extend_schema(
        summary="Eliminar lógicamente ubicación (soft delete)",
        description=(
            "Marca la ubicación como eliminada lógicamente (deleted_at=now). "
            "El registro NO se elimina de la base de datos ni afecta el historial de movimientos. "
            "Para restaurarla use POST /locations/{id}/restore/."
        ),
        responses={
            204: OpenApiResponse(description="Ubicación eliminada lógicamente."),
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def delete(self, request, pk):
        soft_delete_location(request.user, UUID(str(pk)), request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LocationRestoreView(APIView):
    """POST — Restaura una ubicación previamente eliminada lógicamente."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Restaurar ubicación",
        description="Restaura una ubicación previamente eliminada lógicamente.",
        tags=[TAG_INVENTORY],
        responses={
            200: LocationSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        get_object_or_404(Location, pk=pk)
        loc = restore_location(request.user, UUID(str(pk)), request=request)
        return Response(LocationSerializer(loc).data)


class LocationStateTransitionView(APIView):
    """POST transición formal de estado operativo para una ubicación."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Cambiar estado de ubicación",
        description="Cambia el estado operativo de una ubicación.",
        request=LocationStateTransitionSerializer,
        responses={
            200: LocationSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def post(self, request, pk):
        ser = LocationStateTransitionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        loc = transition_location_state(
            request.user,
            UUID(str(pk)),
            ser.validated_data["operational_status"],
        )
        return Response(LocationSerializer(loc).data, status=status.HTTP_200_OK)


class StockByProductView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Stock por producto",
        description="Consulta el stock consolidado de un producto por ubicación.",
        responses={
            200: StockByProductResponseSerializer,
            **standard_error_responses(include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request, product_id):
        return Response(get_stock_by_product(UUID(str(product_id))))


class StockByLocationView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Stock por ubicación",
        description="Consulta el stock de una ubicación específica.",
        responses={
            200: PaginatedStockByLocationListSerializer,
            **standard_error_responses(include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request, location_id):
        qs = get_stock_by_location(UUID(str(location_id)))
        paginator = ICMPageNumberPagination()
        page = paginator.paginate_queryset(list(qs), request, view=self)
        ser = StockByLocationSerializer(page, many=True)
        return paginator.get_paginated_response(ser.data)


class ReconstructStockView(APIView):
    """POST — Reconstrucción ledger vs stock derivado (solo almacenista)."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Reconstruir stock",
        description="Reconstruye el stock derivado desde el ledger para un producto y ubicación.",
        request=StockReconstructRequestSerializer,
        responses={
            200: StockReconstructResponseSerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_INVENTORY],
    )
    def post(self, request):
        ser = StockReconstructRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        result = trigger_stock_reconstruction(
            request.user, d["product_id"], d["location_id"]
        )
        return Response(result, status=status.HTTP_200_OK)


class ProductSearchView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Buscar productos",
        description="Busca productos por SKU, código de barras o nombre.",
        parameters=[
            OpenApiParameter(
                name="q",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Texto para SKU, código de barras o nombre.",
            ),
            OpenApiParameter(
                name="category",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="brand",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={
            200: PaginatedProductListSerializer,
            **standard_error_responses(),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request):
        q = request.query_params.get("q", "")
        category = request.query_params.get("category")
        brand = request.query_params.get("brand")
        try:
            cat_uuid = UUID(category) if category else None
        except (ValueError, AttributeError):
            raise ValidationError({"category": "UUID inválido."})
        try:
            brand_uuid = UUID(brand) if brand else None
        except (ValueError, AttributeError):
            raise ValidationError({"brand": "UUID inválido."})
        qs = search_products(
            q,
            category_id=cat_uuid,
            brand_id=brand_uuid,
        )
        paginator = ICMPageNumberPagination()
        page = paginator.paginate_queryset(list(qs), request, view=self)
        ser = ProductSerializer(page, many=True)
        return paginator.get_paginated_response(ser.data)


class StockThresholdView(APIView):
    """PATCH — Actualiza el umbral de reorden por ubicación (NEW-02)."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Actualizar umbral de reorden",
        description="Actualiza el umbral de reorden de un stock por ubicación.",
        request=StockThresholdSerializer,
        responses={
            200: StockByLocationSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def patch(self, request, pk):
        from django.shortcuts import get_object_or_404

        row = get_object_or_404(StockByLocation, pk=pk)
        old_value = row.location_reorder_point
        ser = StockThresholdSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        row.location_reorder_point = ser.validated_data["location_reorder_point"]
        row.save(update_fields=["location_reorder_point", "updated_at"])
        log_event(
            AuditEventType.STOCK_THRESHOLD_UPDATED,
            user=request.user,
            detail={
                "stock_id": str(row.id),
                "product_id": str(row.product_id),
                "location_id": str(row.location_id),
                "old_reorder_point": old_value,
                "new_reorder_point": row.location_reorder_point,
                "_entity_type": "StockByLocation",
                "_entity_id": str(row.id),
                "_origin": "API",
            },
        )
        return Response(StockByLocationSerializer(row).data)
