"""Vistas de catálogo (RF-003)."""

from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Brand, Category, Product, ProductCombo
from apps.catalog.permissions import IsAlmacenistaOrReadOnly
from apps.catalog.serializers import (
    BrandCreateSerializer,
    BrandSerializer,
    BrandUpdateSerializer,
    CategoryCreateSerializer,
    CategorySerializer,
    CategoryUpdateSerializer,
    ComboCreateSerializer,
    ComboSerializer,
    ComboUpdateSerializer,
    ProductBarcodeSerializer,
    ProductCreateSerializer,
    ProductDetailSerializer,
    ProductPriceHistorySerializer,
    ProductPriceUpdateSerializer,
    ProductSerializer,
    ProductUpdateSerializer,
    ResolveIdentifierQuerySerializer,
)
from apps.catalog.services import (
    create_brand,
    create_category,
    create_combo,
    create_product,
    disable_brand_for_assignment,
    disable_category_for_assignment,
    disable_product_for_assignment,
    enable_brand_for_assignment,
    enable_category_for_assignment,
    enable_product_for_assignment,
    resolve_identifier,
    restore_brand,
    restore_category,
    restore_combo,
    restore_product,
    soft_delete_brand,
    soft_delete_category,
    soft_delete_combo,
    soft_delete_product,
    update_brand,
    update_category,
    update_combo,
    update_product,
    update_product_prices,
)
from shared.openapi import TAG_CATALOG, standard_error_responses
from shared.pagination import ICMPageNumberPagination
from shared.permissions import IsAlmacenista


@extend_schema_view(
    get=extend_schema(
        summary="Listar categorías",
        description="Lista las categorías registradas en el catálogo.",
        tags=[TAG_CATALOG],
        parameters=[
            OpenApiParameter(
                name="status",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Filtro de estado: active (defecto), inactive, deleted, all. "
                    "'deleted' devuelve solo archivadas; 'all' incluye todas."
                ),
            ),
            OpenApiParameter(
                name="include_inactive",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Si es true, devuelve activas e inactivas (excluye archivadas).",
            ),
        ],
        responses={
            200: CategorySerializer(many=True),
            **standard_error_responses(),
        },
    ),
    post=extend_schema(
        summary="Crear categoría",
        description="Crea una nueva categoría de catálogo.",
        request=CategoryCreateSerializer,
        responses={
            201: CategorySerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_CATALOG],
    ),
)
class CategoryListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrReadOnly)
    serializer_class = CategorySerializer
    pagination_class = ICMPageNumberPagination

    def get_queryset(self):
        qs = Category.objects.all()
        status = self.request.query_params.get("status", "active")
        include_inactive = self.request.query_params.get(
            "include_inactive", ""
        ).lower() in ("1", "true", "yes")

        if include_inactive:
            return qs.filter(deleted_at__isnull=True)

        if status == "all":
            return qs
        if status == "deleted":
            return qs.filter(deleted_at__isnull=False)
        if status == "inactive":
            return qs.filter(is_active=False, deleted_at__isnull=True)
        return qs.filter(is_active=True, deleted_at__isnull=True)

    def create(self, request, *args, **kwargs):
        ser = CategoryCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        cat = create_category(
            request.user,
            name=d["name"],
            description=d.get("description", ""),
            requires_serial_number=d.get("requires_serial_number", False),
            is_returnable=d.get("is_returnable", False),
            request=request,
        )
        return Response(CategorySerializer(cat).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        summary="Listar marcas",
        description="Lista las marcas registradas en el catálogo.",
        tags=[TAG_CATALOG],
        parameters=[
            OpenApiParameter(
                name="status",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Filtro de estado: active (defecto), inactive, deleted, all. "
                    "'deleted' devuelve solo archivadas; 'all' incluye todas."
                ),
            ),
            OpenApiParameter(
                name="include_inactive",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Si es true, devuelve activas e inactivas (excluye archivadas).",
            ),
        ],
        responses={
            200: BrandSerializer(many=True),
            **standard_error_responses(),
        },
    ),
    post=extend_schema(
        summary="Crear marca",
        description="Crea una nueva marca independiente de categorías.",
        request=BrandCreateSerializer,
        responses={
            201: BrandSerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_CATALOG],
    ),
)
class BrandListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrReadOnly)
    serializer_class = BrandSerializer
    pagination_class = ICMPageNumberPagination

    def get_queryset(self):
        qs = Brand.objects.all()
        status = self.request.query_params.get("status", "active")
        include_inactive = self.request.query_params.get(
            "include_inactive", ""
        ).lower() in ("1", "true", "yes")

        if include_inactive:
            return qs.filter(deleted_at__isnull=True)

        if status == "all":
            return qs
        if status == "deleted":
            return qs.filter(deleted_at__isnull=False)
        if status == "inactive":
            return qs.filter(is_active=False, deleted_at__isnull=True)
        return qs.filter(is_active=True, deleted_at__isnull=True)

    def create(self, request, *args, **kwargs):
        ser = BrandCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        try:
            brand = create_brand(
                request.user,
                name=d["name"],
                description=d.get("description", ""),
                request=request,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(BrandSerializer(brand).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        summary="Listar productos",
        description="Lista los productos disponibles en el catálogo.",
        tags=[TAG_CATALOG],
        parameters=[
            OpenApiParameter(
                name="include_archived",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Si es true, incluye productos eliminados lógicamente (deleted_at != null).",
            ),
            OpenApiParameter(
                name="include_inactive",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Si es true, incluye productos con is_active=False.",
            ),
            OpenApiParameter(
                name="category",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filtra por UUID de categoría.",
            ),
            OpenApiParameter(
                name="search",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Búsqueda por nombre o SKU.",
            ),
        ],
        responses={
            200: ProductSerializer(many=True),
            **standard_error_responses(include_403=True),
        },
    ),
    post=extend_schema(
        summary="Crear producto",
        description="Registra un nuevo producto en el catálogo.",
        request=ProductCreateSerializer,
        responses={
            201: ProductSerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_CATALOG],
    ),
)
class ProductListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)
    serializer_class = ProductSerializer
    pagination_class = ICMPageNumberPagination

    def get_queryset(self):
        qs = Product.objects.select_related("category", "brand").all()
        include_archived = self.request.query_params.get(
            "include_archived", ""
        ).lower() in ("1", "true", "yes")
        if not include_archived:
            qs = qs.filter(deleted_at__isnull=True)
        include_inactive = self.request.query_params.get("include_inactive", "").lower()
        if include_inactive not in ("1", "true", "yes"):
            qs = qs.filter(is_active=True)
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category_id=category)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(sku__icontains=search))
        return qs

    def create(self, request, *args, **kwargs):
        ser = ProductCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        product = create_product(request.user, ser.validated_data, request=request)
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        summary="Detalle de producto",
        description="Obtiene el detalle completo de un producto.",
        tags=[TAG_CATALOG],
        responses={
            200: ProductDetailSerializer,
            **standard_error_responses(include_404=True),
        },
    ),
    put=extend_schema(
        summary="Actualizar producto",
        description="Reemplaza la información editable del producto.",
        tags=[TAG_CATALOG],
        responses={
            200: ProductDetailSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    ),
    patch=extend_schema(
        summary="Actualizar producto parcialmente",
        description="Actualiza solo los campos enviados del producto.",
        tags=[TAG_CATALOG],
        responses={
            200: ProductDetailSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    ),
    delete=extend_schema(
        summary="Eliminar lógicamente producto (soft delete)",
        description=(
            "Marca el producto como eliminado lógicamente (deleted_at=now). "
            "El registro NO se elimina de la base de datos ni afecta el historial de movimientos. "
            "Devuelve HTTP 409 si el producto tiene stock, OC activas, recepciones en borrador o combos activos. "
            "Para restaurarlo use POST /products/{id}/restore/."
        ),
        tags=[TAG_CATALOG],
        responses={
            204: None,
            **standard_error_responses(
                include_403=True, include_404=True, include_409=True
            ),
        },
    ),
)
class ProductDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrReadOnly)
    queryset = Product.objects.select_related("category", "brand")
    serializer_class = ProductSerializer
    http_method_names = ["get", "put", "patch", "delete", "head", "options"]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        ser = ProductUpdateSerializer(data=request.data, partial=partial)
        ser.is_valid(raise_exception=True)
        payload = {k: v for k, v in ser.validated_data.items()}
        product = update_product(request.user, instance.pk, payload, request=request)
        return Response(ProductDetailSerializer(product).data)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            soft_delete_product(request.user, instance.pk, request=request)
        except ValueError as exc:
            return Response(
                {"error": "CONFLICT", "message": str(exc), "detail": {}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductBarcodeView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Obtener barcode de producto",
        description=(
            "Devuelve el payload completo del barcode para que el frontend lo consuma "
            "sin reconstruir SVG ni metadata."
        ),
        responses={
            200: ProductBarcodeSerializer,
            **standard_error_responses(include_404=True),
        },
        tags=[TAG_CATALOG],
    )
    def get(self, request, pk):
        product = get_object_or_404(
            Product.objects.select_related("category", "brand"), pk=pk
        )
        return Response(ProductBarcodeSerializer.from_product(product))


class ResolveIdentifierView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Resolver identificador de producto",
        description="Resuelve un identificador flexible a un producto del catálogo.",
        parameters=[
            OpenApiParameter(
                name="q",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="SKU, código de barras o fragmento de nombre.",
            ),
            OpenApiParameter(
                name="identifier",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Alias de `q` (misma semántica).",
            ),
        ],
        responses={
            200: ProductDetailSerializer,
            **standard_error_responses(include_404=True),
        },
        tags=[TAG_CATALOG],
    )
    def get(self, request):
        qser = ResolveIdentifierQuerySerializer(data=request.query_params)
        qser.is_valid(raise_exception=True)
        product = resolve_identifier(qser.validated_data["_value"])
        return Response(ProductDetailSerializer(product).data)


@extend_schema_view(
    get=extend_schema(
        summary="Listar combos",
        description="Lista los combos de productos registrados.",
        tags=[TAG_CATALOG],
        parameters=[
            OpenApiParameter(
                name="include_archived",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Si es true, incluye combos eliminados lógicamente (deleted_at != null).",
            ),
        ],
        responses={
            200: ComboSerializer(many=True),
            **standard_error_responses(),
        },
    ),
    post=extend_schema(
        summary="Crear combo",
        description="Crea un nuevo combo de productos.",
        request=ComboCreateSerializer,
        responses={
            201: ComboSerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_CATALOG],
    ),
)
class ComboListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrReadOnly)
    serializer_class = ComboSerializer
    pagination_class = ICMPageNumberPagination

    def get_queryset(self):
        qs = ProductCombo.objects.prefetch_related("combo_items__product").all()
        include_archived = self.request.query_params.get(
            "include_archived", ""
        ).lower() in ("1", "true", "yes")
        if not include_archived:
            qs = qs.filter(deleted_at__isnull=True)
        return qs

    def create(self, request, *args, **kwargs):
        ser = ComboCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        combo = create_combo(request.user, ser.validated_data, request=request)
        return Response(ComboSerializer(combo).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        summary="Detalle de categoría",
        description="Obtiene el detalle de una categoría.",
        tags=[TAG_CATALOG],
        responses={
            200: CategorySerializer,
            **standard_error_responses(include_404=True),
        },
    ),
    put=extend_schema(
        summary="Actualizar categoría",
        description="Reemplaza los datos editables de una categoría.",
        request=CategoryUpdateSerializer,
        tags=[TAG_CATALOG],
        responses={
            200: CategorySerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    ),
    patch=extend_schema(
        summary="Actualizar categoría parcialmente",
        description="Actualiza solo los campos enviados de una categoría.",
        request=CategoryUpdateSerializer,
        tags=[TAG_CATALOG],
        responses={
            200: CategorySerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    ),
    delete=extend_schema(
        summary="Eliminar lógicamente categoría (soft delete)",
        description=(
            "Archiva la categoría (deleted_at=now). "
            "El registro NO se elimina de la base de datos ni del historial de movimientos. "
            "Devuelve HTTP 409 si la categoría tiene productos activos asociados. "
            "Para restaurarla use POST /categories/{id}/restore/. "
            "Para solo deshabilitar (is_active=False sin archivar) use POST /categories/{id}/disable/."
        ),
        tags=[TAG_CATALOG],
        responses={
            204: None,
            **standard_error_responses(include_403=True, include_404=True),
        },
    ),
)
class CategoryDetailView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrReadOnly)

    def _get_category(self, pk):
        return get_object_or_404(Category, pk=pk)

    def get(self, request, pk):
        return Response(CategorySerializer(self._get_category(pk)).data)

    def put(self, request, pk):
        ser = CategoryUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            cat = update_category(request.user, pk, ser.validated_data, request=request)
        except ObjectDoesNotExist:
            raise NotFound()
        return Response(CategorySerializer(cat).data)

    def patch(self, request, pk):
        ser = CategoryUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        try:
            cat = update_category(request.user, pk, ser.validated_data, request=request)
        except ObjectDoesNotExist:
            raise NotFound()
        return Response(CategorySerializer(cat).data)

    def delete(self, request, pk):
        try:
            soft_delete_category(request.user, pk, request=request)
        except ObjectDoesNotExist:
            raise NotFound()
        except ValueError as exc:
            return Response(
                {"error": "CONFLICT", "message": str(exc), "detail": {}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryRestoreView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Restaurar categoría",
        description="Restaura una categoría eliminada lógicamente.",
        tags=[TAG_CATALOG],
        responses={
            200: CategorySerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        try:
            cat = restore_category(request.user, pk, request=request)
        except ObjectDoesNotExist:
            raise NotFound()
        except ValueError as exc:
            return Response(
                {"error": "CONFLICT", "message": str(exc), "detail": {}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(CategorySerializer(cat).data)


@extend_schema_view(
    get=extend_schema(
        summary="Detalle de marca",
        description="Obtiene el detalle de una marca.",
        tags=[TAG_CATALOG],
        responses={
            200: BrandSerializer,
            **standard_error_responses(include_404=True),
        },
    ),
    put=extend_schema(
        summary="Actualizar marca",
        description="Reemplaza los datos editables de una marca.",
        request=BrandUpdateSerializer,
        tags=[TAG_CATALOG],
        responses={
            200: BrandSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    ),
    patch=extend_schema(
        summary="Actualizar marca parcialmente",
        description="Actualiza solo los campos enviados de una marca.",
        request=BrandUpdateSerializer,
        tags=[TAG_CATALOG],
        responses={
            200: BrandSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    ),
    delete=extend_schema(
        summary="Eliminar lógicamente marca (soft delete)",
        description=(
            "Archiva la marca (deleted_at=now). "
            "El registro NO se elimina de la base de datos ni del historial de movimientos. "
            "Devuelve HTTP 409 si la marca tiene productos activos asociados. "
            "Para restaurarla use POST /brands/{id}/restore/. "
            "Para solo deshabilitar (is_active=False sin archivar) use POST /brands/{id}/disable/."
        ),
        tags=[TAG_CATALOG],
        responses={
            204: None,
            **standard_error_responses(include_403=True, include_404=True),
        },
    ),
)
class BrandDetailView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrReadOnly)

    def _get_brand(self, pk):
        return get_object_or_404(Brand, pk=pk)

    def get(self, request, pk):
        return Response(BrandSerializer(self._get_brand(pk)).data)

    def put(self, request, pk):
        ser = BrandUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            brand = update_brand(request.user, pk, ser.validated_data, request=request)
        except ObjectDoesNotExist:
            raise NotFound()
        return Response(BrandSerializer(brand).data)

    def patch(self, request, pk):
        ser = BrandUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        try:
            brand = update_brand(request.user, pk, ser.validated_data, request=request)
        except ObjectDoesNotExist:
            raise NotFound()
        return Response(BrandSerializer(brand).data)

    def delete(self, request, pk):
        try:
            soft_delete_brand(request.user, pk, request=request)
        except ObjectDoesNotExist:
            raise NotFound()
        except ValueError as exc:
            return Response(
                {"error": "CONFLICT", "message": str(exc), "detail": {}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class BrandRestoreView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Restaurar marca",
        description="Restaura una marca eliminada lógicamente.",
        tags=[TAG_CATALOG],
        responses={
            200: BrandSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        try:
            brand = restore_brand(request.user, pk, request=request)
        except ObjectDoesNotExist:
            raise NotFound()
        except ValueError as exc:
            return Response(
                {"error": "CONFLICT", "message": str(exc), "detail": {}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(BrandSerializer(brand).data)


class CategoryDisableView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Desactivar categoría para asignación",
        description=(
            "Marca is_active=False. La categoría no puede asignarse a nuevos productos "
            "pero conserva todas las relaciones históricas. Nunca bloquea."
        ),
        tags=[TAG_CATALOG],
        responses={
            200: CategorySerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        try:
            cat = disable_category_for_assignment(request.user, pk, request=request)
        except ObjectDoesNotExist:
            raise NotFound()
        except ValueError as exc:
            return Response(
                {"error": "CONFLICT", "message": str(exc), "detail": {}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(CategorySerializer(cat).data)


class CategoryEnableView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Reactivar categoría para asignación",
        description="Marca is_active=True. La categoría vuelve a estar disponible para nuevos productos.",
        tags=[TAG_CATALOG],
        responses={
            200: CategorySerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        try:
            cat = enable_category_for_assignment(request.user, pk, request=request)
        except ObjectDoesNotExist:
            raise NotFound()
        except ValueError as exc:
            return Response(
                {"error": "CONFLICT", "message": str(exc), "detail": {}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(CategorySerializer(cat).data)


class BrandDisableView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Desactivar marca para asignación",
        description=(
            "Marca is_active=False. La marca no puede asignarse a nuevos productos "
            "pero conserva todas las relaciones históricas. Nunca bloquea."
        ),
        tags=[TAG_CATALOG],
        responses={
            200: BrandSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        try:
            brand = disable_brand_for_assignment(request.user, pk, request=request)
        except ObjectDoesNotExist:
            raise NotFound()
        except ValueError as exc:
            return Response(
                {"error": "CONFLICT", "message": str(exc), "detail": {}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(BrandSerializer(brand).data)


class BrandEnableView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Reactivar marca para asignación",
        description="Marca is_active=True. La marca vuelve a estar disponible para nuevos productos.",
        tags=[TAG_CATALOG],
        responses={
            200: BrandSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        try:
            brand = enable_brand_for_assignment(request.user, pk, request=request)
        except ObjectDoesNotExist:
            raise NotFound()
        except ValueError as exc:
            return Response(
                {"error": "CONFLICT", "message": str(exc), "detail": {}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(BrandSerializer(brand).data)


@extend_schema_view(
    get=extend_schema(
        summary="Detalle de combo",
        description="Obtiene el detalle de un combo de productos.",
        tags=[TAG_CATALOG],
        responses={200: ComboSerializer, **standard_error_responses(include_404=True)},
    ),
    put=extend_schema(
        summary="Actualizar combo",
        description=(
            "Reemplaza los datos de un combo. "
            "Si se envían `items`, los ComboItems anteriores son **eliminados permanentemente** "
            "de la base de datos (hard delete) y reemplazados por los nuevos."
        ),
        request=ComboUpdateSerializer,
        tags=[TAG_CATALOG],
        responses={
            200: ComboSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    ),
    patch=extend_schema(
        summary="Actualizar combo parcialmente",
        description=(
            "Actualiza solo los campos enviados. "
            "Si se envían `items`, los ComboItems anteriores son **eliminados permanentemente** "
            "de la base de datos (hard delete) y reemplazados por los nuevos."
        ),
        request=ComboUpdateSerializer,
        tags=[TAG_CATALOG],
        responses={
            200: ComboSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    ),
    delete=extend_schema(
        summary="Eliminar lógicamente combo (soft delete)",
        description=(
            "Marca el combo como eliminado lógicamente (deleted_at=now). "
            "El registro NO se elimina de la base de datos ni afecta sus productos componentes. "
            "Para restaurarlo use POST /combos/{id}/restore/."
        ),
        tags=[TAG_CATALOG],
        responses={
            204: None,
            **standard_error_responses(include_403=True, include_404=True),
        },
    ),
)
class ComboDetailView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrReadOnly)

    def _get_combo(self, pk):
        return get_object_or_404(
            ProductCombo.objects.prefetch_related("combo_items__product"), pk=pk
        )

    def get(self, request, pk):
        return Response(ComboSerializer(self._get_combo(pk)).data)

    def put(self, request, pk):
        ser = ComboUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            combo = update_combo(request.user, pk, ser.validated_data, request=request)
        except ObjectDoesNotExist:
            raise NotFound()
        return Response(ComboSerializer(combo).data)

    def patch(self, request, pk):
        ser = ComboUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        try:
            combo = update_combo(request.user, pk, ser.validated_data, request=request)
        except ObjectDoesNotExist:
            raise NotFound()
        return Response(ComboSerializer(combo).data)

    def delete(self, request, pk):
        try:
            soft_delete_combo(request.user, pk, request=request)
        except ObjectDoesNotExist:
            raise NotFound()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ComboRestoreView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Restaurar combo",
        description="Restaura un combo de productos previamente eliminado lógicamente.",
        tags=[TAG_CATALOG],
        responses={
            200: ComboSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        get_object_or_404(ProductCombo, pk=pk)
        combo = restore_combo(request.user, pk, request=request)
        return Response(ComboSerializer(combo).data)


class ProductRestoreView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Restaurar producto",
        description="Restaura un producto previamente eliminado lógicamente.",
        tags=[TAG_CATALOG],
        responses={
            200: ProductDetailSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        get_object_or_404(Product, pk=pk)
        product = restore_product(request.user, pk, request=request)
        return Response(ProductDetailSerializer(product).data)


class ProductDisableView(APIView):
    """POST — Desactiva un producto para asignación (pausa temporal)."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Desactivar producto para asignación",
        description=(
            "Marca el producto como inactivo para asignación (pausa temporal). "
            "El producto NO se elimina y puede reactivarse con POST /enable/."
        ),
        tags=[TAG_CATALOG],
        responses={
            200: ProductDetailSerializer,
            409: None,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        get_object_or_404(Product, pk=pk)
        product = disable_product_for_assignment(request.user, pk, request=request)
        return Response(ProductDetailSerializer(product).data)


class ProductEnableView(APIView):
    """POST — Reactiva un producto para asignación."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Activar producto para asignación",
        description="Reactiva un producto previamente desactivado para asignación (pausa).",
        tags=[TAG_CATALOG],
        responses={
            200: ProductDetailSerializer,
            409: None,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        get_object_or_404(Product, pk=pk)
        try:
            product = enable_product_for_assignment(request.user, pk, request=request)
        except ValueError as exc:
            return Response(
                {"error": "CONFLICT", "message": str(exc), "detail": {}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(ProductDetailSerializer(product).data)


class ProductPricesView(APIView):
    """PATCH /catalog/products/<id>/prices/ — gestión de precios (solo almacenista)."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Configurar precios de un producto",
        description=(
            "Actualiza unit_cost, sale_price_retail, sale_price_wholesale, tax_rate_pct y/o currency. "
            "Solo los campos enviados se modifican. Registra historial inmutable de cada cambio (BR-17)."
        ),
        request=ProductPriceUpdateSerializer,
        responses={
            200: ProductSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_CATALOG],
    )
    def patch(self, request, pk):
        get_object_or_404(Product, pk=pk)
        ser = ProductPriceUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        product = update_product_prices(
            request.user,
            pk,
            unit_cost=d.get("unit_cost"),
            sale_price_retail=d.get("sale_price_retail"),
            sale_price_wholesale=d.get("sale_price_wholesale"),
            tax_rate_pct=d.get("tax_rate_pct"),
            currency=d.get("currency"),
            request=request,
        )
        return Response(ProductSerializer(product).data)

    @extend_schema(
        summary="Historial de precios de un producto",
        description="Retorna el historial inmutable de cambios de precio del producto.",
        responses={
            200: ProductPriceHistorySerializer(many=True),
            **standard_error_responses(include_404=True),
        },
        tags=[TAG_CATALOG],
    )
    def get(self, request, pk):
        from apps.catalog.models import ProductPriceHistory

        product = get_object_or_404(Product, pk=pk)
        history = ProductPriceHistory.objects.filter(product=product).select_related(
            "changed_by"
        )
        return Response(ProductPriceHistorySerializer(history, many=True).data)
