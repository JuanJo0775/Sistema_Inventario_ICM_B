from apps.movements.views import (
    AdjustmentListCreateView,
    DispatchListCreateView,
    EntryListCreateView,
    MovementListView,
)


def test_movement_views_are_available():
    assert MovementListView is not None
    assert EntryListCreateView is not None
    assert DispatchListCreateView is not None
    assert AdjustmentListCreateView is not None
