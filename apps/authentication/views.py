"""Vistas de autenticación (RF-001, RF-002)."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from drf_spectacular.utils import (OpenApiResponse, extend_schema,
                                   extend_schema_view)
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.authentication.serializers import (ICMTokenObtainPairSerializer,
                                             ICMTokenRefreshSerializer,
                                             LoginRequestSerializer,
                                             UserCreateSerializer,
                                             UserSerializer)
from apps.authentication.services import (create_user, disable_user,
                                          update_user, update_user_password)
from shared.openapi import TAG_AUTH, TAG_SYSTEM, standard_error_responses
from shared.permissions import IsAlmacenista, IsAlmacenistaOrAdministrador

User = get_user_model()


@extend_schema(
    summary="Iniciar sesión (JWT)",
    description=(
        "RF-001, BR-03 — Envíe `password` y `username` **o** `email`. "
        "Respuesta: `access`, `refresh` y objeto `user` (perfil sin contraseña). "
        "Los auxiliares de despacho solo pueden autenticarse en franja operativa."
    ),
    tags=[TAG_AUTH],
    auth=[],
    request=LoginRequestSerializer,
    responses={
        200: OpenApiResponse(
            response={
                "type": "object",
                "properties": {
                    "access": {"type": "string"},
                    "refresh": {"type": "string"},
                    "user": {"type": "object"},
                },
            },
            description="Tokens JWT y perfil de usuario.",
        ),
        **standard_error_responses(include_403=True, include_500=True),
    },
)
class ICMTokenObtainPairView(TokenObtainPairView):
    serializer_class = ICMTokenObtainPairSerializer


@extend_schema(
    summary="Renovar access token",
    description=(
        "Envía el `refresh` emitido en el login para obtener un nuevo `access`. "
        "RF-001, BR-03 — Auxiliar de despacho: renovación rechazada fuera de franja operativa "
        "(07:00–12:00 y 14:00–17:00, America/Bogota)."
    ),
    tags=[TAG_AUTH],
    auth=[],
    responses={
        200: OpenApiResponse(description="Nuevo access token generado."),
        **standard_error_responses(include_403=True),
    },
)
class ICMTokenRefreshView(TokenRefreshView):
    serializer_class = ICMTokenRefreshSerializer


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Cerrar sesión (blacklist refresh)",
        description="RF-002 — Invalida el refresh token enviado en el cuerpo.",
        tags=[TAG_AUTH],
        request=None,
        responses={
            204: OpenApiResponse(description="Sesión cerrada correctamente."),
            **standard_error_responses(),
        },
    )
    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            raise ValidationError({"refresh": ["Debe proporcionar el token refresh."]})

        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except TokenError as exc:
            raise ValidationError(
                {"refresh": ["El token refresh es inválido, expiró o ya fue revocado."]}
            ) from exc
        log_event(
            AuditEventType.LOGOUT,
            description="Cierre de sesión",
            user=request.user,
            request=request,
            detail={},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    summary="Perfil del usuario autenticado",
    tags=[TAG_AUTH],
    responses={
        200: UserSerializer,
        **standard_error_responses(),
    },
)
class MeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserListCreateView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(
        summary="Listar usuarios",
        description="Solo almacenista (RF-002, BR-02).",
        tags=[TAG_AUTH],
        responses={
            200: UserSerializer(many=True),
            **standard_error_responses(include_403=True),
        },
    )
    def get(self, request):
        from apps.authentication.selectors import get_all_users

        users = get_all_users(request.user)
        return Response(UserSerializer(users, many=True).data)

    @extend_schema(
        summary="Crear usuario",
        description="Solo almacenista. Requiere username, email, password y rol.",
        tags=[TAG_AUTH],
        request=UserCreateSerializer,
        responses={
            201: UserSerializer,
            **standard_error_responses(include_403=True),
        },
    )
    def post(self, request):
        ser = UserCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = create_user(request.user, ser.validated_data, request=request)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(
        summary="Detalle de usuario",
        tags=[TAG_AUTH],
        responses={
            200: UserSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def get(self, request, pk):
        from apps.authentication.selectors import get_user_by_id

        user = get_user_by_id(pk)
        return Response(UserSerializer(user).data)

    @extend_schema(
        summary="Actualizar usuario",
        tags=[TAG_AUTH],
        request=UserSerializer,
        responses={
            200: UserSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    @extend_schema(
        summary="Actualizar usuario (parcial)",
        tags=[TAG_AUTH],
        request=UserSerializer,
        responses={
            200: UserSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial: bool):
        from apps.authentication.selectors import get_user_by_id

        instance = get_user_by_id(pk)
        data = dict(request.data)
        password = data.pop("password", None)
        if password:
            if isinstance(password, list):
                password = password[0]
            update_user_password(request.user, instance.id, password, request=request)

        serializer = UserSerializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated = update_user(
            request.user, instance.id, serializer.validated_data, request=request
        )
        return Response(UserSerializer(updated).data)


class UserDisableView(APIView):
    """POST — Deshabilitar usuario (contrato README_API §10.1, RF-002)."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Deshabilitar usuario",
        description="RF-002 — Revoca sesiones (blacklist) y marca la cuenta inactiva.",
        tags=[TAG_AUTH],
        request=None,
        responses={
            204: OpenApiResponse(description="Usuario deshabilitado exitosamente."),
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        disable_user(request.user, pk, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    summary="Health check",
    description="Comprobación de disponibilidad del servicio (sin autenticación).",
    tags=[TAG_SYSTEM],
    auth=[],
    responses={
        200: {
            "type": "object",
            "properties": {"status": {"type": "string", "example": "ok"}},
        }
    },
)
class HealthCheckView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({"status": "ok"})
