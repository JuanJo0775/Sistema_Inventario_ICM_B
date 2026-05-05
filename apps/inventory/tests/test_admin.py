"""
Administración Django alineada a BR-11 (stock derivado solo vía ledger).

Criterio de negocio alineado con `docs/ERS_ICM_Requisitos.md` RF-004 / BR-11 y
`docs/ICM_Informe_Elicitacion_v2_plus.docx.md`: el stock por ubicación es derivado
del ledger; no debe alterarse manualmente como si fuera fuente de verdad.
"""

from django.contrib.admin.sites import AdminSite

from apps.inventory.admin import StockByLocationAdmin
from apps.inventory.models import StockByLocation


def test_stock_by_location_admin_is_least_privilege_derived_stock():
    site = AdminSite()
    ma = StockByLocationAdmin(StockByLocation, site)
    assert ma.has_add_permission(None) is False
    assert ma.has_delete_permission(None) is False
    assert "current_stock" in ma.readonly_fields
    assert "product" in ma.readonly_fields
