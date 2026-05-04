from django.urls import path

from apps.reports.views import MovementHistoryReportView, MovementSummaryReportView, SalesSummaryReportView

urlpatterns = [
    path("movements/summary/", MovementSummaryReportView.as_view(), name="reports-movements-summary"),
    path("sales/summary/", SalesSummaryReportView.as_view(), name="reports-sales-summary"),
    path("movements/history/", MovementHistoryReportView.as_view(), name="reports-movements-history"),
]
