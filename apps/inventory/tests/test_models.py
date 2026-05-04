from apps.inventory.models import Location, StockByLocation


def test_inventory_models_define_location_and_stock_cache():
    assert Location._meta.model_name == "location"
    assert StockByLocation._meta.model_name == "stockbylocation"
