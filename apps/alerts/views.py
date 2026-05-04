from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.alerts.models import Alert
from apps.alerts.serializers import AlertSerializer
from shared.openapi import TAG_ALERTS
from shared.pagination import ICMPageNumberPagination
from shared.permissions import IsAlmacenistaOrAdministrador


class AlertListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)
    serializer_class = AlertSerializer
    pagination_class = ICMPageNumberPagination

    def get_queryset(self):
        return Alert.objects.select_related("product").filter(is_active=True).order_by("-created_at")

    @extend_schema(responses={200: AlertSerializer(many=True)}, tags=[TAG_ALERTS])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
