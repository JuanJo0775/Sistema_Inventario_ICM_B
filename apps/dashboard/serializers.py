from __future__ import annotations

from rest_framework import serializers


class DashboardMetricSummarySerializer(serializers.Serializer):
    stock_total = serializers.IntegerField()
    dispatches_today = serializers.IntegerField()
    reorder_count = serializers.IntegerField()
    invoices_issued = serializers.IntegerField()
    invoice_range = serializers.CharField(allow_null=True)


class DashboardAlertSummarySerializer(serializers.Serializer):
    active = serializers.IntegerField()
    reorder = serializers.IntegerField()
    expiring = serializers.IntegerField()
    expiring_days = serializers.IntegerField()
    returns = serializers.IntegerField()


class DashboardKPIValueSerializer(serializers.Serializer):
    label = serializers.CharField()
    value = serializers.FloatField(allow_null=True)
    unit = serializers.CharField()
    precision = serializers.ChoiceField(
        choices=("real", "partial", "approximate", "future")
    )
    threshold = serializers.FloatField(allow_null=True)
    source = serializers.CharField()


class DashboardKPISummarySerializer(serializers.Serializer):
    warehouse_utilization = DashboardKPIValueSerializer()
    damaged_rate = DashboardKPIValueSerializer()
    return_rate = DashboardKPIValueSerializer()
    dispatch_invoice_ratio = DashboardKPIValueSerializer()
    discard_rate = DashboardKPIValueSerializer()
    cold_chain_alerts = DashboardKPIValueSerializer()


class DashboardMovementSerializer(serializers.Serializer):
    id = serializers.CharField()
    type = serializers.CharField()
    title = serializers.CharField()
    sku = serializers.CharField()
    quantity = serializers.IntegerField()
    user = serializers.CharField()
    time = serializers.CharField()
    status = serializers.CharField()


class DashboardOverviewSerializer(serializers.Serializer):
    metrics = DashboardMetricSummarySerializer()
    alerts = DashboardAlertSummarySerializer()
    kpis = DashboardKPISummarySerializer()
    movements = DashboardMovementSerializer(many=True)
    generated_at = serializers.DateTimeField()
