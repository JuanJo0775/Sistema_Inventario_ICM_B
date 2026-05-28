from django.urls import path

from apps.movements.views import (
    AdjustmentCorrectView,
    AdjustmentListCreateView,
    ComboDispatchView,
    DispatchDetailView,
    DispatchInvoiceDownloadView,
    DispatchListCreateView,
    EntryDetailView,
    EntryListCreateView,
    MovementCorrectionView,
    MovementDetailView,
    MovementListView,
    ReturnListCreateView,
    TransferListCreateView,
)

urlpatterns = [
    path(
        "combo-dispatch/", ComboDispatchView.as_view(), name="movements-combo-dispatch"
    ),
    path("entries/", EntryListCreateView.as_view(), name="movements-entries"),
    path(
        "entries/<uuid:pk>/", EntryDetailView.as_view(), name="movements-entry-detail"
    ),
    path("dispatches/", DispatchListCreateView.as_view(), name="movements-dispatches"),
    path(
        "dispatches/<uuid:pk>/",
        DispatchDetailView.as_view(),
        name="movements-dispatch-detail",
    ),
    path(
        "dispatches/<uuid:pk>/invoice/",
        DispatchInvoiceDownloadView.as_view(),
        name="movements-dispatch-invoice",
    ),
    path("transfers/", TransferListCreateView.as_view(), name="movements-transfers"),
    path("returns/", ReturnListCreateView.as_view(), name="movements-returns"),
    path(
        "adjustments/correct/",
        AdjustmentCorrectView.as_view(),
        name="movements-adjustments-correct",
    ),
    path(
        "adjustments/", AdjustmentListCreateView.as_view(), name="movements-adjustments"
    ),
    path(
        "<uuid:pk>/corrections/",
        MovementCorrectionView.as_view(),
        name="movements-corrections",
    ),
    path("<uuid:pk>/", MovementDetailView.as_view(), name="movements-detail"),
    path("", MovementListView.as_view(), name="movements-list"),
]
