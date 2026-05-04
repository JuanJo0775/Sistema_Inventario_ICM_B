from django.urls import path

from apps.movements.views import (
    AdjustmentCreateView,
    DispatchCreateView,
    EntryCreateView,
    MovementCorrectionView,
    MovementDetailView,
    MovementListView,
    ReturnApproveView,
    ReturnCreateView,
    ReturnRejectView,
    TransferCreateView,
)

urlpatterns = [
    path("", MovementListView.as_view(), name="movements-list"),
    path("entries/", EntryCreateView.as_view(), name="movements-entries"),
    path("dispatches/", DispatchCreateView.as_view(), name="movements-dispatches"),
    path("transfers/", TransferCreateView.as_view(), name="movements-transfers"),
    path("returns/", ReturnCreateView.as_view(), name="movements-returns"),
    path("returns/<uuid:pk>/approve/", ReturnApproveView.as_view(), name="movements-returns-approve"),
    path("returns/<uuid:pk>/reject/", ReturnRejectView.as_view(), name="movements-returns-reject"),
    path("adjustments/", AdjustmentCreateView.as_view(), name="movements-adjustments"),
    path("<uuid:pk>/corrections/", MovementCorrectionView.as_view(), name="movements-corrections"),
    path("<uuid:pk>/", MovementDetailView.as_view(), name="movements-detail"),
]
