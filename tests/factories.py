"""Factories reutilizables en pruebas."""

from __future__ import annotations

from datetime import timedelta

import factory
from django.contrib.auth import get_user_model
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.authentication.models import UserRole
from apps.catalog.models import Category, Lot, Product
from apps.inventory.models import Location

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    # Set password via explicit post_generation hook to control save behavior

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        pwd = extracted or "testpass123"
        obj.set_password(pwd)
        if create:
            obj.save()

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

    # Generar SKUs válidos según el nuevo patrón: 1-4 letras, guion, 1-4 dígitos
    sku = factory.Sequence(lambda n: f"PRD-{n%9999+1:04d}")
    name = factory.Faker("word")
    category = factory.SubFactory(ManoCategoryFactory)
    barcode = factory.SelfAttribute("sku")
    brand = "Can"
    reorder_point = 5
    requires_expiration = False


class LotFactory(DjangoModelFactory):
    class Meta:
        model = Lot

    product = factory.SubFactory(ProductFactory)
    code = factory.Sequence(lambda n: f"LOT-{n:04d}")
    expiration_date = factory.LazyFunction(
        lambda: timezone.now().date() + timedelta(days=180)
    )


class LocationFactory(DjangoModelFactory):
    class Meta:
        model = Location

    name = factory.Sequence(lambda n: f"Ubicación {n}")
    code = factory.Sequence(lambda n: f"LOC-{n:04d}")
    description = ""
    is_retail = False
