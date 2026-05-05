from apps.catalog.views import CategoryListCreateView, ProductListCreateView, ResolveIdentifierView


def test_catalog_views_are_available():
    assert CategoryListCreateView is not None
    assert ProductListCreateView is not None
    assert ResolveIdentifierView is not None
