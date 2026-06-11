"""Vistas REST para gestión de webhooks (NEW-03)."""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.webhooks.models import WebhookDelivery, WebhookEndpoint
from apps.webhooks.serializers import (
    WebhookDeliverySerializer,
    WebhookEndpointCreateSerializer,
    WebhookEndpointSerializer,
    WebhookTestSerializer,
)
from apps.webhooks.services import _attempt_delivery
from shared.openapi import TAG_WEBHOOKS, standard_error_responses
from shared.pagination import ICMPageNumberPagination
from shared.permissions import IsAlmacenista


class WebhookEndpointListCreateView(APIView):
    """GET/POST — Lista y crea endpoints de webhook (solo administradores)."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Listar endpoints de webhook",
        description="Lista los endpoints de webhook configurados.",
        responses={
            200: WebhookEndpointSerializer(many=True),
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_WEBHOOKS],
    )
    def get(self, request):
        qs = WebhookEndpoint.objects.all().order_by("-created_at")
        paginator = ICMPageNumberPagination()
        page = paginator.paginate_queryset(list(qs), request, view=self)
        return paginator.get_paginated_response(
            WebhookEndpointSerializer(page, many=True).data
        )

    @extend_schema(
        summary="Crear endpoint de webhook",
        description="Crea un nuevo endpoint de webhook.",
        request=WebhookEndpointCreateSerializer,
        responses={
            201: WebhookEndpointSerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_WEBHOOKS],
    )
    def post(self, request):
        ser = WebhookEndpointCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        endpoint = WebhookEndpoint.objects.create(
            url=d["url"],
            secret=d["secret"],
            events=d["events"],
            is_active=d.get("is_active", True),
            max_retries=d.get("max_retries", 3),
            created_by=request.user,
        )
        log_event(
            AuditEventType.WEBHOOK_ENDPOINT_CHANGED,
            user=request.user,
            detail={
                "endpoint_id": str(endpoint.id),
                "_entity_type": "WebhookEndpoint",
                "_entity_id": str(endpoint.id),
                "_origin": "API",
                "_action": "created",
            },
        )
        return Response(
            WebhookEndpointSerializer(endpoint).data, status=status.HTTP_201_CREATED
        )


class WebhookEndpointDetailView(APIView):
    """GET/PUT/PATCH/DELETE — Detalle de un endpoint de webhook."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Detalle de endpoint de webhook",
        description="Obtiene el detalle de un endpoint de webhook.",
        responses={
            200: WebhookEndpointSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_WEBHOOKS],
    )
    def get(self, request, pk):
        return Response(
            WebhookEndpointSerializer(get_object_or_404(WebhookEndpoint, pk=pk)).data
        )

    @extend_schema(
        summary="Reemplazar endpoint de webhook",
        description="Reemplaza completamente los datos de un endpoint de webhook.",
        request=WebhookEndpointCreateSerializer,
        responses={
            200: WebhookEndpointSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_WEBHOOKS],
    )
    def put(self, request, pk):
        endpoint = get_object_or_404(WebhookEndpoint, pk=pk)
        ser = WebhookEndpointCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        for field, value in ser.validated_data.items():
            setattr(endpoint, field, value)
        endpoint.save()
        log_event(
            AuditEventType.WEBHOOK_ENDPOINT_CHANGED,
            user=request.user,
            detail={
                "endpoint_id": str(endpoint.id),
                "_entity_type": "WebhookEndpoint",
                "_entity_id": str(endpoint.id),
                "_origin": "API",
                "_action": "updated",
            },
        )
        return Response(WebhookEndpointSerializer(endpoint).data)

    @extend_schema(
        summary="Actualizar endpoint de webhook",
        description="Actualiza parcialmente un endpoint de webhook.",
        request=WebhookEndpointCreateSerializer,
        responses={
            200: WebhookEndpointSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_WEBHOOKS],
    )
    def patch(self, request, pk):
        endpoint = get_object_or_404(WebhookEndpoint, pk=pk)
        ser = WebhookEndpointCreateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        for field, value in ser.validated_data.items():
            setattr(endpoint, field, value)
        endpoint.save()
        log_event(
            AuditEventType.WEBHOOK_ENDPOINT_CHANGED,
            user=request.user,
            detail={
                "endpoint_id": str(endpoint.id),
                "_entity_type": "WebhookEndpoint",
                "_entity_id": str(endpoint.id),
                "_origin": "API",
                "_action": "updated",
            },
        )
        return Response(WebhookEndpointSerializer(endpoint).data)

    @extend_schema(
        summary="Desactivar endpoint de webhook",
        description=(
            "Marca el endpoint como inactivo: deja de recibir eventos. "
            "El registro NO se elimina de la base de datos ni se pierden las entregas registradas."
        ),
        responses={
            204: None,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_WEBHOOKS],
    )
    def delete(self, request, pk):
        endpoint = get_object_or_404(WebhookEndpoint, pk=pk)
        endpoint.is_active = False
        endpoint.save(update_fields=["is_active", "updated_at"])
        log_event(
            AuditEventType.WEBHOOK_ENDPOINT_CHANGED,
            user=request.user,
            detail={
                "endpoint_id": str(endpoint.id),
                "_entity_type": "WebhookEndpoint",
                "_entity_id": str(endpoint.id),
                "_origin": "API",
                "_action": "deactivated",
            },
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class WebhookTestView(APIView):
    """POST — Envía un payload de prueba al endpoint."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Probar endpoint de webhook",
        description="Envía un payload de prueba al endpoint de webhook.",
        request=WebhookTestSerializer,
        responses={
            200: None,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_WEBHOOKS],
    )
    def post(self, request, pk):
        endpoint = get_object_or_404(WebhookEndpoint, pk=pk)
        ser = WebhookTestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        delivery = WebhookDelivery(
            endpoint=endpoint,
            event_type=ser.validated_data.get("event_type", "TEST"),
            payload=ser.validated_data.get("payload", {}),
            status=WebhookDelivery.Status.PENDING,
            next_retry_at=timezone.now(),
        )
        delivery.save()
        _attempt_delivery(delivery)
        return Response(
            {"status": delivery.status, "response_code": delivery.response_code}
        )


class WebhookDeliveryListView(APIView):
    """GET — Historial de entregas de webhooks."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Historial de entregas de webhook",
        description="Lista el historial de entregas de webhooks.",
        responses={
            200: WebhookDeliverySerializer(many=True),
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_WEBHOOKS],
    )
    def get(self, request):
        qs = WebhookDelivery.objects.select_related("endpoint").order_by("-created_at")
        paginator = ICMPageNumberPagination()
        page = paginator.paginate_queryset(list(qs), request, view=self)
        return paginator.get_paginated_response(
            WebhookDeliverySerializer(page, many=True).data
        )


class WebhookStatsView(APIView):
    """GET — Métricas de entregas de webhooks."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Métricas de webhooks",
        description="Obtiene métricas agregadas de entregas de webhooks.",
        responses={
            200: inline_serializer(
                name="WebhookStatsResponse",
                fields={
                    "pending": serializers.IntegerField(),
                    "delivered": serializers.IntegerField(),
                    "failed": serializers.IntegerField(),
                    "active_endpoints": serializers.IntegerField(),
                },
            )
        },
        tags=[TAG_WEBHOOKS],
    )
    def get(self, request):
        return Response(
            {
                "pending": WebhookDelivery.objects.filter(
                    status=WebhookDelivery.Status.PENDING
                ).count(),
                "delivered": WebhookDelivery.objects.filter(
                    status=WebhookDelivery.Status.DELIVERED
                ).count(),
                "failed": WebhookDelivery.objects.filter(
                    status=WebhookDelivery.Status.FAILED
                ).count(),
                "active_endpoints": WebhookEndpoint.objects.filter(
                    is_active=True
                ).count(),
            }
        )
