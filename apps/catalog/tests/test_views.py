from apps.catalog.views import CategoryListView, ProductListCreateView, ResolveIdentifierView


def test_catalog_views_are_available():
    assert CategoryListView is not None
    assert ProductListCreateView is not None
    assert ResolveIdentifierView is not None
