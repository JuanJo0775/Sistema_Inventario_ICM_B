from __future__ import annotations

from rest_framework import serializers


class ReportRangeSerializer(serializers.Serializer):
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()


class MovementSummaryResponseSerializer(serializers.Serializer):
    counts = serializers.DictField(child=serializers.IntegerField())


class SalesTotalsSerializer(serializers.Serializer):
    mayor = serializers.IntegerField()
    menor = serializers.IntegerField()


class SalesSummaryResponseSerializer(serializers.Serializer):
    sales = SalesTotalsSerializer()


class InventorySummaryItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    sku = serializers.CharField()
    name = serializers.CharField()
    total_stock = serializers.IntegerField()


class MovementReportItemSerializer(serializers.Serializer):
    movement_type = serializers.CharField()
    count = serializers.IntegerField()
    total_quantity = serializers.IntegerField()


class TopDispatchedProductSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    sku = serializers.CharField()
    name = serializers.CharField()
    dispatched_quantity = serializers.IntegerField()


class KpiDashboardSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    active_alerts = serializers.IntegerField()
    movements_today = serializers.IntegerField()
    low_stock_items = serializers.IntegerField()
