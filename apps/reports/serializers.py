"""Serializadores para los endpoints de `reports`.

Nota: el serializer `KpiDashboardSerializer` representa el payload del panel
legacy de KPI. El origen de la verdad de las métricas se encuentra en
`apps.dashboard.services` (función `build_legacy_kpi_panel` y los builders
del módulo `apps.dashboard.services`). Si se modifica la forma del panel en
el servicio del dashboard, actualizar este serializer para mantener la
compatibilidad con el endpoint `reports/kpi/` y con `ReportDatasetView`.
"""

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
    category_id = serializers.UUIDField()
    category = serializers.CharField()
    total_units = serializers.IntegerField()


class InventorySummaryResponseSerializer(serializers.Serializer):
    by_category = InventorySummaryItemSerializer(many=True)
    products_with_zero_stock = serializers.IntegerField()
    approximate_value = serializers.FloatField(allow_null=True)
    approximate_value_note = serializers.CharField()


class MovementReportProductItemSerializer(serializers.Serializer):
    product__sku = serializers.CharField()
    product__name = serializers.CharField()
    total_qty = serializers.IntegerField()


class MovementReportUserItemSerializer(serializers.Serializer):
    executed_by__username = serializers.CharField()
    movements = serializers.IntegerField()


class MovementReportPeriodSerializer(serializers.Serializer):
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()


class MovementReportResponseSerializer(serializers.Serializer):
    counts = serializers.DictField(child=serializers.IntegerField())
    by_product = MovementReportProductItemSerializer(many=True)
    by_user = MovementReportUserItemSerializer(many=True)
    period = MovementReportPeriodSerializer()


class LegacyMovementReportItemSerializer(serializers.Serializer):
    """Contrato histórico por ítem; mantenido para compatibilidad temporal."""

    movement_type = serializers.CharField()
    count = serializers.IntegerField()
    total_quantity = serializers.IntegerField()


class TopDispatchedProductSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    sku = serializers.CharField()
    name = serializers.CharField()
    dispatched_quantity = serializers.IntegerField()


class ExpiringLotReportItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    sku = serializers.CharField()
    name = serializers.CharField()
    lot_id = serializers.UUIDField()
    lot_code = serializers.CharField()
    expiration_date = serializers.DateField()
    days_left = serializers.IntegerField()
    location_id = serializers.UUIDField()
    location_code = serializers.CharField()
    location_name = serializers.CharField()
    available_quantity = serializers.IntegerField()


class WarehouseUtilizationLocationSerializer(serializers.Serializer):
    location_id = serializers.UUIDField()
    code = serializers.CharField()
    name = serializers.CharField()
    occupied_units = serializers.IntegerField()
    capacity_units = serializers.IntegerField(allow_null=True)
    utilization_pct = serializers.FloatField(allow_null=True)
    is_retail = serializers.BooleanField()
    capacity_configured = serializers.BooleanField()
    capacity_mode = serializers.CharField()
    capacity_level = serializers.IntegerField(allow_null=True)
    capacity_score = serializers.IntegerField(allow_null=True)
    occupancy_estimate_pct = serializers.FloatField(allow_null=True)
    operational_status = serializers.CharField()
    storage_type_code = serializers.CharField(allow_null=True)
    storage_type_name = serializers.CharField(allow_null=True)


class WarehouseUtilizationStorageTypeSerializer(serializers.Serializer):
    storage_type_code = serializers.CharField()
    storage_type_name = serializers.CharField()
    locations = serializers.IntegerField()
    occupied_units = serializers.IntegerField()


class WarehouseUtilizationOperationalStatusSerializer(serializers.Serializer):
    operational_status = serializers.CharField()
    locations = serializers.IntegerField()
    occupied_units = serializers.IntegerField()


class WarehouseUtilizationSummarySerializer(serializers.Serializer):
    occupied_units = serializers.IntegerField()
    capacity_units = serializers.IntegerField()
    utilization_pct = serializers.FloatField(allow_null=True)
    configured_locations = serializers.IntegerField()
    locations_without_capacity = serializers.IntegerField()
    unconfigured_occupied_units = serializers.IntegerField()


class WarehouseUtilizationResponseSerializer(serializers.Serializer):
    overall = WarehouseUtilizationSummarySerializer()
    by_location = WarehouseUtilizationLocationSerializer(many=True)
    by_storage_type = WarehouseUtilizationStorageTypeSerializer(many=True)
    by_operational_status = WarehouseUtilizationOperationalStatusSerializer(many=True)


class QualityOperationalItemSerializer(serializers.Serializer):
    movement_type = serializers.CharField()
    product_sku = serializers.CharField()
    product_name = serializers.CharField()
    movements = serializers.IntegerField()
    units = serializers.IntegerField()


class QualityOperationalTypeSerializer(serializers.Serializer):
    movement_type = serializers.CharField()
    movements = serializers.IntegerField()
    units = serializers.IntegerField()


class QualityOperationalTotalsSerializer(serializers.Serializer):
    movements = serializers.IntegerField()
    units = serializers.IntegerField()


class QualityOperationalBreakdownSerializer(serializers.Serializer):
    incident_units = serializers.IntegerField()
    damage_units = serializers.IntegerField()
    discard_units = serializers.IntegerField()
    return_units = serializers.IntegerField()
    quality_index_pct = serializers.FloatField()


class QualityOperationalPeriodSerializer(serializers.Serializer):
    days = serializers.IntegerField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()


class QualityOperationalResponseSerializer(serializers.Serializer):
    period = QualityOperationalPeriodSerializer()
    totals = QualityOperationalTotalsSerializer()
    breakdown = QualityOperationalBreakdownSerializer()
    by_type = QualityOperationalTypeSerializer(many=True)
    by_product = QualityOperationalItemSerializer(many=True)
    notes = serializers.ListField(child=serializers.CharField())


class DiscardOperationalSummarySerializer(serializers.Serializer):
    period = QualityOperationalPeriodSerializer()
    totals = QualityOperationalTotalsSerializer()
    by_type = QualityOperationalTypeSerializer(many=True)
    by_product = QualityOperationalItemSerializer(many=True)
    notes = serializers.ListField(child=serializers.CharField())


class DispatchOperationalSummarySerializer(serializers.Serializer):
    period = QualityOperationalPeriodSerializer()
    sales = SalesTotalsSerializer()
    invoice_linked_dispatches = serializers.IntegerField()
    movement_counts = serializers.DictField(child=serializers.IntegerField())
    top_products = TopDispatchedProductSerializer(many=True)
    notes = serializers.ListField(child=serializers.CharField())
    shipments = serializers.IntegerField()
    invoice_linked_ratio = serializers.FloatField()
    order_proxy = serializers.JSONField(allow_null=True)
    carriers = serializers.JSONField(allow_null=True)
    per_order_samples = serializers.ListField(child=serializers.JSONField())
    promised_date_example = serializers.DateTimeField(allow_null=True)


class PerOrderSampleSerializer(serializers.Serializer):
    invoice_number = serializers.CharField()
    movements = serializers.IntegerField()
    total_quantity = serializers.IntegerField()
    items = serializers.IntegerField()
    dispatched_at = serializers.DateTimeField(allow_null=True)


class KpiDashboardSerializer(serializers.Serializer):
    movements_today = serializers.IntegerField()
    low_stock_products_count = serializers.IntegerField()
    active_alerts_unresolved = serializers.IntegerField()
    dispatches_this_month = serializers.IntegerField()
    generated_at = serializers.DateTimeField()


class ReportDatasetSerializer(serializers.Serializer):
    report = serializers.CharField()
    generated_at = serializers.DateTimeField()
    filters = serializers.JSONField()
    data = serializers.JSONField()
    suggested_filename = serializers.CharField()
