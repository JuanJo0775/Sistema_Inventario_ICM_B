"""Vistas REST para gestión de webhooks (NEW-03)."""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
        return Response(
            WebhookEndpointSerializer(endpoint).data, status=status.HTTP_201_CREATED
        )


class WebhookEndpointDetailView(APIView):
    """GET/PATCH/DELETE — Detalle de un endpoint de webhook."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
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
        return Response(WebhookEndpointSerializer(endpoint).data)

    @extend_schema(
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
        return Response(status=status.HTTP_204_NO_CONTENT)


class WebhookTestView(APIView):
    """POST — Envía un payload de prueba al endpoint."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
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

    @extend_schema(tags=[TAG_WEBHOOKS])
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
