from apps.movements.views import AdjustmentCreateView, DispatchCreateView, EntryCreateView, MovementListView


def test_movement_views_are_available():
    assert MovementListView is not None
    assert EntryCreateView is not None
    assert DispatchCreateView is not None
    assert AdjustmentCreateView is not None
