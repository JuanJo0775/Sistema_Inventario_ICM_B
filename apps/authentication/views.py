"""Vistas de autenticación (RF-001, RF-002)."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.authentication.serializers import ICMTokenObtainPairSerializer, UserCreateSerializer, UserSerializer
from apps.authentication.services import create_user, disable_user, update_user_password
from shared.openapi import TAG_AUTH, TAG_SYSTEM
from shared.permissions import IsAlmacenista

User = get_user_model()


@extend_schema(
    summary="Iniciar sesión (JWT)",
    description=(
        "RF-001, BR-03 — Devuelve `access`, `refresh` y datos básicos del usuario. "
        "Los auxiliares de despacho solo pueden autenticarse en franja operativa."
    ),
    tags=[TAG_AUTH],
    auth=[],
)
class ICMTokenObtainPairView(TokenObtainPairView):
    serializer_class = ICMTokenObtainPairSerializer


@extend_schema(
    summary="Renovar access token",
    description="Envía el `refresh` emitido en el login para obtener un nuevo `access`.",
    tags=[TAG_AUTH],
    auth=[],
)
class ICMTokenRefreshView(TokenRefreshView):
    pass


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Cerrar sesión (blacklist refresh)",
        description="RF-002 — Invalida el refresh token enviado en el cuerpo.",
        tags=[TAG_AUTH],
        request=None,
        responses={204: None},
    )
    def post(self, request):
        refresh = request.data.get("refresh")
        if refresh:
            try:
                token = RefreshToken(refresh)
                token.blacklist()
            except Exception:
                pass
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    get=extend_schema(
        summary="Perfil del usuario autenticado",
        tags=[TAG_AUTH],
    ),
)
class MeView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


@extend_schema_view(
    get=extend_schema(
        summary="Listar usuarios",
        description="Solo almacenista (RF-002, BR-02).",
        tags=[TAG_AUTH],
    ),
    post=extend_schema(
        summary="Crear usuario",
        description="Solo almacenista. Cuerpo: username, password, role, etc.",
        tags=[TAG_AUTH],
        request=UserCreateSerializer,
        responses={201: UserSerializer},
    ),
)
class UserListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)
    queryset = User.objects.all().order_by("-created_at")
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserCreateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        ser = UserCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = create_user(request.user, ser.validated_data, request=request)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(summary="Detalle de usuario", tags=[TAG_AUTH]),
    put=extend_schema(summary="Actualizar usuario", tags=[TAG_AUTH]),
    patch=extend_schema(summary="Actualizar usuario (parcial)", tags=[TAG_AUTH]),
)
class UserDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        data = dict(request.data)
        password = data.pop("password", None)
        if password:
            update_user_password(request.user, instance.id, password, request=request)
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserDisableView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Deshabilitar usuario",
        description="RF-002 — Revoca tokens y desactiva la cuenta.",
        tags=[TAG_AUTH],
        request=None,
        responses={204: None},
    )
    def post(self, request, pk: int):
        disable_user(request.user, int(pk), request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    summary="Health check",
    description="Comprobación de disponibilidad del servicio (sin autenticación).",
    tags=[TAG_SYSTEM],
    auth=[],
    responses={200: {"type": "object", "properties": {"status": {"type": "string", "example": "ok"}}}},
)
class HealthCheckView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({"status": "ok"})
