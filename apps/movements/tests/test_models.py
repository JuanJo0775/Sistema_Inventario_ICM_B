from apps.movements.models import MovementType


def test_movement_type_labels():
    assert MovementType.ENTRADA == "ENTRADA"
