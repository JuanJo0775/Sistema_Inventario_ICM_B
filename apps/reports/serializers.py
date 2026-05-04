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
