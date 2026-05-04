from apps.catalog.services import resolve_identifier


def test_catalog_service_exports_identifier_resolver():
    assert callable(resolve_identifier)
