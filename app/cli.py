"""Custom Flask CLI commands (database seeding and reset)."""

from decimal import Decimal

import click
from flask import Flask

from app.extensions import db
from app.models import Category, Order, OrderItem, OrderStatus, Product

CATEGORIES = [
    {"name": "Electronics", "description": "Phones, laptops and gadgets"},
    {"name": "Books", "description": "Printed and digital books"},
    {"name": "Home & Kitchen", "description": "Appliances and utensils"},
    {"name": "Sports", "description": "Equipment and apparel"},
]

PRODUCTS = [
    # (name, sku, price, stock, category name)
    ("Wireless Mouse", "ELEC-001", "89.90", 120, "Electronics"),
    ("Mechanical Keyboard", "ELEC-002", "349.00", 45, "Electronics"),
    ("27\" Monitor", "ELEC-003", "1299.90", 18, "Electronics"),
    ("Noise Cancelling Headphones", "ELEC-004", "799.00", 30, "Electronics"),
    ("Clean Code", "BOOK-001", "159.90", 60, "Books"),
    ("The Pragmatic Programmer", "BOOK-002", "179.90", 25, "Books"),
    ("Designing Data-Intensive Applications", "BOOK-003", "249.90", 12, "Books"),
    ("Espresso Machine", "HOME-001", "1899.00", 8, "Home & Kitchen"),
    ("Chef Knife Set", "HOME-002", "459.90", 22, "Home & Kitchen"),
    ("Air Fryer 5L", "HOME-003", "649.00", 15, "Home & Kitchen"),
    ("Running Shoes", "SPRT-001", "529.90", 40, "Sports"),
    ("Yoga Mat", "SPRT-002", "129.90", 75, "Sports"),
]

ORDERS = [
    # (customer name, email, status, [(sku, quantity)])
    ("Alice Johnson", "alice@example.com", OrderStatus.PENDING,
     [("ELEC-001", 2), ("BOOK-001", 1)]),
    ("Bruno Costa", "bruno@example.com", OrderStatus.PAID,
     [("ELEC-003", 1), ("ELEC-004", 1)]),
    ("Carla Mendes", "carla@example.com", OrderStatus.SHIPPED,
     [("HOME-003", 1), ("SPRT-002", 3)]),
]


def register_commands(app: Flask) -> None:
    """Attach the custom commands to the application."""

    @app.cli.command("seed")
    @click.option("--reset", is_flag=True, help="Wipe existing data before seeding.")
    def seed(reset: bool) -> None:
        """Populate the database with demo data."""
        if reset:
            _wipe()
        if db.session.query(Category.query.exists()).scalar():
            click.echo("Database already has data. Use --reset to wipe it first.")
            return

        categories = {c["name"]: Category(**c) for c in CATEGORIES}
        db.session.add_all(categories.values())
        db.session.flush()

        products: dict[str, Product] = {}
        for name, sku, price, stock, category_name in PRODUCTS:
            product = Product(
                name=name,
                sku=sku,
                description=f"{name} - demo record created by the seed command.",
                price=Decimal(price),
                stock=stock,
                is_active=True,
                category=categories[category_name],
            )
            products[sku] = product
        db.session.add_all(products.values())
        db.session.flush()

        for customer_name, email, status, lines in ORDERS:
            order = Order(
                customer_name=customer_name, customer_email=email, status=status
            )
            for sku, quantity in lines:
                product = products[sku]
                product.stock -= quantity  # seeded orders reserve stock too
                order.items.append(
                    OrderItem(
                        product=product,
                        quantity=quantity,
                        unit_price=Decimal(product.price),
                    )
                )
            order.recalculate_total()
            db.session.add(order)

        db.session.commit()
        click.echo(
            f"Seeded {len(categories)} categories, {len(products)} products "
            f"and {len(ORDERS)} orders."
        )

    @app.cli.command("wipe")
    def wipe_command() -> None:
        """Delete every row without dropping the schema."""
        _wipe()
        click.echo("All data removed.")


def _wipe() -> None:
    """Delete rows honoring the foreign key order."""
    OrderItem.query.delete()
    Order.query.delete()
    Product.query.delete()
    Category.query.delete()
    db.session.commit()
