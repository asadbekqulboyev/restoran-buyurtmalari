from __future__ import annotations

import json
import os
import shlex
import tempfile
from dataclasses import asdict, dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Callable


MONEY_PLACES = Decimal("0.01")


def money(value: Decimal | str | int | float) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


@dataclass
class Table:
    number: int
    seats: int


@dataclass
class Dish:
    name: str
    price: Decimal
    category: str


@dataclass
class OrderItem:
    dish_name: str
    quantity: int
    unit_price: Decimal

    @property
    def total(self) -> Decimal:
        return money(self.unit_price * self.quantity)


@dataclass
class Order:
    table_number: int
    items: list[OrderItem] = field(default_factory=list)
    loyalty: bool = False


class RestaurantError(ValueError):
    pass


class RestaurantApp:
    def __init__(self, data_file: str | Path = "restaurant_data.json") -> None:
        self.data_file = Path(data_file)
        self.tables: dict[int, Table] = {}
        self.menu: dict[str, Dish] = {}
        self.orders: dict[int, Order] = {}
        self.closed_bills: list[dict[str, str | int]] = []
        self.load()

    def add_table(self, number: int, seats: int) -> None:
        if number <= 0 or seats <= 0:
            raise RestaurantError("Stol raqami va o'rinlar soni musbat bo'lishi kerak.")
        if number in self.tables:
            raise RestaurantError("Bu stol allaqachon mavjud.")
        self.tables[number] = Table(number, seats)
        self.save()

    def add_dish(self, name: str, price: Decimal | str | int | float, category: str) -> None:
        price = money(price)
        if not name.strip() or price <= 0:
            raise RestaurantError("Taom nomi bo'sh va narx musbat bo'lishi kerak.")
        if category not in {"ovqat", "ichimlik"}:
            raise RestaurantError("Turkum faqat 'ovqat' yoki 'ichimlik' bo'lishi mumkin.")
        if name in self.menu:
            raise RestaurantError("Bu taom allaqachon mavjud.")
        self.menu[name] = Dish(name, price, category)
        self.save()

    def open_order(self, table_number: int, loyalty: bool = False) -> None:
        self._require_table(table_number)
        if table_number in self.orders:
            raise RestaurantError("Bu stolda ochiq buyurtma mavjud.")
        self.orders[table_number] = Order(table_number, loyalty=loyalty)
        self.save()

    def add_item(self, table_number: int, dish_name: str, quantity: int = 1) -> None:
        order = self._require_order(table_number)
        dish = self.menu.get(dish_name)
        if dish is None:
            raise RestaurantError("Menyuda bunday taom yo'q.")
        if quantity <= 0:
            raise RestaurantError("Miqdor musbat bo'lishi kerak.")
        for item in order.items:
            if item.dish_name == dish_name:
                item.quantity += quantity
                break
        else:
            order.items.append(OrderItem(dish.name, quantity, dish.price))
        self.save()

    def remove_item(self, table_number: int, dish_name: str, quantity: int = 1) -> None:
        order = self._require_order(table_number)
        if quantity <= 0:
            raise RestaurantError("Miqdor musbat bo'lishi kerak.")
        for item in order.items:
            if item.dish_name == dish_name:
                if quantity > item.quantity:
                    raise RestaurantError("Olib tashlanadigan miqdor mavjudidan ko'p.")
                item.quantity -= quantity
                if item.quantity == 0:
                    order.items.remove(item)
                self.save()
                return
        raise RestaurantError("Buyurtmada bunday pozitsiya yo'q.")

    def calculate_bill(self, table_number: int, guests: int = 1) -> dict[str, Decimal | int]:
        order = self._require_order(table_number)
        if guests <= 0:
            raise RestaurantError("Mehmonlar soni musbat bo'lishi kerak.")
        subtotal = money(sum((item.total for item in order.items), Decimal("0")))
        service = money(subtotal * Decimal("0.10"))
        discount = money((subtotal + service) * Decimal("0.15")) if order.loyalty else money(0)
        total = money(subtotal + service - discount)
        return {"subtotal": subtotal, "service": service, "discount": discount,
                "total": total, "guests": guests, "per_guest": money(total / guests)}

    def close_order(self, table_number: int, guests: int = 1) -> dict[str, Decimal | int]:
        bill = self.calculate_bill(table_number, guests)
        self.closed_bills.append({"table": table_number, "total": str(bill["total"])})
        del self.orders[table_number]
        self.save()
        return bill

    def save(self) -> None:
        payload = {
            "tables": [asdict(table) for table in self.tables.values()],
            "menu": [{**asdict(dish), "price": str(dish.price)} for dish in self.menu.values()],
            "orders": [{"table_number": order.table_number, "loyalty": order.loyalty,
                        "items": [{**asdict(item), "unit_price": str(item.unit_price)}
                                  for item in order.items]}
                       for order in self.orders.values()],
            "closed_bills": self.closed_bills,
        }
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(dir=self.data_file.parent, prefix=".restaurant-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump(payload, file, ensure_ascii=False, indent=2)
            os.replace(temporary_name, self.data_file)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)

    def load(self) -> None:
        if not self.data_file.exists():
            return
        with self.data_file.open(encoding="utf-8") as file:
            payload = json.load(file)
        self.tables = {item["number"]: Table(**item) for item in payload.get("tables", [])}
        self.menu = {item["name"]: Dish(item["name"], money(item["price"]), item["category"])
                     for item in payload.get("menu", [])}
        self.orders = {}
        for item in payload.get("orders", []):
            order = Order(item["table_number"], loyalty=item.get("loyalty", False))
            order.items = [OrderItem(entry["dish_name"], entry["quantity"], money(entry["unit_price"]))
                           for entry in item.get("items", [])]
            self.orders[order.table_number] = order
        self.closed_bills = payload.get("closed_bills", [])

    def _require_table(self, table_number: int) -> Table:
        if table_number not in self.tables:
            raise RestaurantError("Bunday stol mavjud emas.")
        return self.tables[table_number]

    def _require_order(self, table_number: int) -> Order:
        self._require_table(table_number)
        if table_number not in self.orders:
            raise RestaurantError("Bu stolda ochiq buyurtma yo'q.")
        return self.orders[table_number]


def format_bill(bill: dict[str, Decimal | int]) -> str:
    return (f"Jami: {bill['subtotal']} so'm | Xizmat haqi: {bill['service']} so'm | "
            f"Chegirma: {bill['discount']} so'm | To'lanadi: {bill['total']} so'm | "
            f"Har bir mehmon: {bill['per_guest']} so'm")


def run_cli(app: RestaurantApp) -> None:
    commands: dict[str, Callable[[list[str]], str]] = {
        "add-table": lambda args: _add_table(app, args),
        "add-dish": lambda args: _add_dish(app, args),
        "open": lambda args: _open(app, args),
        "add": lambda args: _add_item(app, args),
        "remove": lambda args: _remove_item(app, args),
        "bill": lambda args: _bill(app, args),
        "close": lambda args: _close(app, args),
    }
    print("Restoran hisob tizimi. Chiqish uchun 'exit' yozing.")
    while True:
        try:
            parts = shlex.split(input("> "))
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not parts:
            continue
        if parts[0] == "exit":
            return
        if parts[0] not in commands:
            print("Noma'lum buyruq. README.md dagi sintaksisdan foydalaning.")
            continue
        try:
            print(commands[parts[0]](parts[1:]))
        except (RestaurantError, ValueError, IndexError) as error:
            print(f"Xato: {error}")


def _add_table(app: RestaurantApp, args: list[str]) -> str:
    app.add_table(int(args[0]), int(args[1]))
    return "Stol qo'shildi."


def _add_dish(app: RestaurantApp, args: list[str]) -> str:
    app.add_dish(args[0], args[1], args[2])
    return "Taom menyuga qo'shildi."


def _open(app: RestaurantApp, args: list[str]) -> str:
    app.open_order(int(args[0]), len(args) > 1 and args[1].lower() in {"ha", "yes", "true"})
    return "Buyurtma ochildi."


def _add_item(app: RestaurantApp, args: list[str]) -> str:
    app.add_item(int(args[0]), args[1], int(args[2]) if len(args) > 2 else 1)
    return "Pozitsiya qo'shildi."


def _remove_item(app: RestaurantApp, args: list[str]) -> str:
    app.remove_item(int(args[0]), args[1], int(args[2]) if len(args) > 2 else 1)
    return "Pozitsiya olib tashlandi."


def _bill(app: RestaurantApp, args: list[str]) -> str:
    return format_bill(app.calculate_bill(int(args[0]), int(args[1]) if len(args) > 1 else 1))


def _close(app: RestaurantApp, args: list[str]) -> str:
    return format_bill(app.close_order(int(args[0]), int(args[1]) if len(args) > 1 else 1))


if __name__ == "__main__":
    run_cli(RestaurantApp())