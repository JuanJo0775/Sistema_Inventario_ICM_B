"""Tests para shared/utils/db.py (ADR-015)."""

from __future__ import annotations

import pytest

from shared.exceptions import ResourceNotFoundError
from shared.utils.db import get_for_update_or_404
from tests.factories import CategoryFactory


@pytest.mark.django_db
def test_get_for_update_or_404_found():
    category = CategoryFactory()
    result = get_for_update_or_404(CategoryFactory._meta.model.objects, pk=category.id)
    assert result.id == category.id
    assert result.name == category.name


@pytest.mark.django_db
def test_get_for_update_or_404_not_found():
    fake_pk = "00000000-0000-0000-0000-000000000000"
    with pytest.raises(ResourceNotFoundError) as exc_info:
        get_for_update_or_404(CategoryFactory._meta.model.objects, pk=fake_pk)
    assert "no encontrado" in str(exc_info.value.message).lower()


@pytest.mark.django_db
def test_get_for_update_or_404_custom_message():
    fake_pk = "00000000-0000-0000-0000-000000000000"
    custom_msg = "Categoría personalizada no existe."
    with pytest.raises(ResourceNotFoundError) as exc_info:
        get_for_update_or_404(
            CategoryFactory._meta.model.objects, pk=fake_pk, detail=custom_msg
        )
    assert exc_info.value.message == custom_msg
