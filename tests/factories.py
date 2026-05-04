"""Factories reutilizables en pruebas."""

from __future__ import annotations

import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from apps.authentication.models import UserRole
from apps.catalog.models import Category, Product
from apps.inventory.models import Location, LocationChoices

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    role = UserRole.AUXILIAR_DESPACHO
    is_active = True


class AlmacenistaFactory(UserFactory):
    role = UserRole.ALMACENISTA


class AdministradorFactory(UserFactory):
    role = UserRole.ADMINISTRADOR


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Categoría {n}")
    slug = factory.Sequence(lambda n: f"categoria-{n}")
    requires_serial_number = False
    is_returnable = False


class ElectroCategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ("slug",)

    name = "Electroterapía"
    slug = "electroterapia"
    requires_serial_number = True
    is_returnable = True


class ManoCategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ("slug",)

    name = "Manoterapía"
    slug = "manoterapia"
    requires_serial_number = False
    is_returnable = False


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    sku = factory.Sequence(lambda n: f"CAN-{n:05d}")
    name = factory.Faker("word")
    category = factory.SubFactory(ManoCategoryFactory)
    barcode = factory.Sequence(lambda n: f"BAR{n:08d}")
    brand = "Can"
    reorder_point = 5


class LocationFactory(DjangoModelFactory):
    class Meta:
        model = Location
        django_get_or_create = ("code",)

    code = factory.Iterator(
        [LocationChoices.VITRINA, LocationChoices.BODEGA_1, LocationChoices.BODEGA_2]
    )
    name = factory.LazyAttribute(lambda o: o.code.replace("_", " ").title())
    description = ""
    is_retail = factory.LazyAttribute(lambda o: o.code == LocationChoices.VITRINA)
