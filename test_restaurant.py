from decimal import Decimal

import pytest

from restaurant import RestaurantApp, RestaurantError


def prepared_app(tmp_path):
    app = RestaurantApp(tmp_path / "data.json")
    app.add_table(1, 4)
    app.add_dish("Osh", "30000", "ovqat")
    app.add_dish("Choy", "10000", "ichimlik")
    return app


def test_add_and_remove_order_item(tmp_path):
    app = prepared_app(tmp_path)
    app.open_order(1)
    app.add_item(1, "Osh", 2)
    app.remove_item(1, "Osh")
    assert app.orders[1].items[0].quantity == 1


def test_one_open_order_per_table(tmp_path):
    app = prepared_app(tmp_path)
    app.open_order(1)
    with pytest.raises(RestaurantError):
        app.open_order(1)


def test_service_fee_is_added(tmp_path):
    app = prepared_app(tmp_path)
    app.open_order(1)
    app.add_item(1, "Osh")
    assert app.calculate_bill(1)["total"] == Decimal("33000.00")


def test_loyalty_discount_and_split(tmp_path):
    app = prepared_app(tmp_path)
    app.open_order(1, loyalty=True)
    app.add_item(1, "Osh")
    bill = app.calculate_bill(1, guests=2)
    assert bill["discount"] == Decimal("4950.00")
    assert bill["per_guest"] == Decimal("14025.00")


def test_data_survives_restart(tmp_path):
    path = tmp_path / "data.json"
    app = RestaurantApp(path)
    app.add_table(7, 2)
    app.add_dish("Suv", "5000", "ichimlik")
    app.open_order(7)
    app.add_item(7, "Suv", 3)
    restored = RestaurantApp(path)
    assert restored.tables[7].seats == 2
    assert restored.orders[7].items[0].quantity == 3