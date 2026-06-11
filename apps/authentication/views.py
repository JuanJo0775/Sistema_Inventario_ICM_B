"""Vistas de autenticación (RF-001, RF-002)."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.authentication.permissions import IsAlmacenista, IsAlmacenistaOrAdministrador
from apps.authentication.serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ICMTokenObtainPairSerializer,
    ICMTokenRefreshSerializer,
    LoginRequestSerializer,
    ResetPasswordSerializer,
    TemporaryAccessPermitSerializer,
    UserCreateSerializer,
    UserScheduleSerializer,
    UserSerializer,
)
from apps.authentication.services import (
    change_own_password,
    create_user,
    disable_user,
    enable_user,
    request_password_reset,
    reset_password_with_token,
    update_user,
    update_user_password,
)
from shared.openapi import TAG_AUTH, TAG_SYSTEM, standard_error_responses

from apps.authentication.models import User


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
    description="Devuelve el perfil del usuario autenticado sin exponer la contraseña.",
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
    def get_permissions(self):
        if self.request.method == "POST":
            permission_classes = (IsAuthenticated, IsAlmacenista)
        else:
            permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)
        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Listar usuarios",
        description=(
            "Almacenista o administrador. Vista de lectura protegida (RF-002, BR-02). "
            "Parámetros opcionales: `include_inactive` (1/true), `role` (almacenista|auxiliar_despacho|administrador), "
            "`search` (username/email/nombre), `page` y `page_size` para paginación."
        ),
        tags=[TAG_AUTH],
        responses={
            200: UserSerializer(many=True),
            **standard_error_responses(include_403=True),
        },
    )
    def get(self, request):
        from apps.authentication.selectors import get_all_users
        from shared.pagination import ICMPageNumberPagination

        params = request.query_params
        users = get_all_users(
            request.user,
            include_inactive=params.get("include_inactive", "").lower()
            in ("1", "true", "yes"),
            role=params.get("role") or None,
            search=params.get("search") or None,
        )
        if "page" in params or "page_size" in params:
            paginator = ICMPageNumberPagination()
            page = paginator.paginate_queryset(users, request)
            if page is not None:
                return paginator.get_paginated_response(
                    UserSerializer(page, many=True).data
                )
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
    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH"}:
            permission_classes = (IsAuthenticated, IsAlmacenista)
        else:
            permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)
        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Detalle de usuario",
        description="Obtiene el detalle de un usuario por su identificador.",
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
        description="Solo almacenista.",
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
        description="Solo almacenista.",
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


class UserEnableView(APIView):
    """POST — Rehabilitar usuario previamente deshabilitado (RF-002)."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Rehabilitar usuario",
        description="RF-002 — Reactiva una cuenta de usuario previamente deshabilitada.",
        tags=[TAG_AUTH],
        request=None,
        responses={
            200: UserSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        from django.shortcuts import get_object_or_404

        get_object_or_404(User, pk=pk)
        user = enable_user(request.user, pk, request=request)
        return Response(UserSerializer(user).data)


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


class UserScheduleDetailView(APIView):
    def get_permissions(self):
        if self.request.method in {"POST", "PUT", "PATCH"}:
            permission_classes = (IsAuthenticated, IsAlmacenista)
        else:
            permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)
        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Ver horario personalizado del usuario",
        description="Obtiene el horario personalizado estable del auxiliar de despacho.",
        tags=[TAG_AUTH],
        responses={
            200: UserScheduleSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def get(self, request, pk):
        from apps.authentication.models import UserSchedule

        target_user = get_object_or_404(User, pk=pk)
        try:
            schedule = UserSchedule.objects.get(user=target_user)
            return Response(UserScheduleSerializer(schedule).data)
        except UserSchedule.DoesNotExist:
            return Response(
                {
                    "detail": "No se ha configurado un horario personalizado para este usuario."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    @extend_schema(
        summary="Configurar horario personalizado del usuario",
        description="Establece o actualiza el horario personalizado estable del auxiliar de despacho (solo almacenista).",
        tags=[TAG_AUTH],
        request=UserScheduleSerializer,
        responses={
            200: UserScheduleSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        from apps.authentication.serializers import UserScheduleSerializer
        from apps.authentication.services import create_or_update_user_schedule

        target_user = get_object_or_404(User, pk=pk)
        serializer = UserScheduleSerializer(
            data=request.data, context={"target_user": target_user}
        )
        serializer.is_valid(raise_exception=True)
        schedule = create_or_update_user_schedule(
            request.user, target_user, serializer.validated_data, request=request
        )
        return Response(UserScheduleSerializer(schedule).data)


class UserTemporaryPermitListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            permission_classes = (IsAuthenticated, IsAlmacenista)
        else:
            permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)
        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Listar permisos temporales de un usuario",
        description="Obtiene la lista de autorizaciones extraordinarias temporales de un auxiliar.",
        tags=[TAG_AUTH],
        responses={
            200: TemporaryAccessPermitSerializer(many=True),
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def get(self, request, pk):
        from apps.authentication.models import TemporaryAccessPermit

        target_user = get_object_or_404(User, pk=pk)
        permits = TemporaryAccessPermit.objects.filter(user=target_user).order_by(
            "-created_at"
        )
        return Response(TemporaryAccessPermitSerializer(permits, many=True).data)

    @extend_schema(
        summary="Otorgar permiso temporal",
        description="Crea una autorización extraordinaria temporal para el auxiliar de despacho (solo almacenista).",
        tags=[TAG_AUTH],
        request=TemporaryAccessPermitSerializer,
        responses={
            201: TemporaryAccessPermitSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        from apps.authentication.serializers import TemporaryAccessPermitSerializer
        from apps.authentication.services import grant_temporary_permit

        target_user = get_object_or_404(User, pk=pk)
        serializer = TemporaryAccessPermitSerializer(
            data=request.data, context={"target_user": target_user}
        )
        serializer.is_valid(raise_exception=True)
        permit = grant_temporary_permit(
            request.user, target_user, serializer.validated_data, request=request
        )
        return Response(
            TemporaryAccessPermitSerializer(permit).data,
            status=status.HTTP_201_CREATED,
        )


class TemporaryPermitRevokeView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Revocar permiso temporal",
        description="Revoca (marca como inactivo) una autorización extraordinaria temporal (solo almacenista).",
        tags=[TAG_AUTH],
        request=None,
        responses={
            200: TemporaryAccessPermitSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    )
    def post(self, request, pk):
        from apps.authentication.models import TemporaryAccessPermit
        from apps.authentication.serializers import TemporaryAccessPermitSerializer
        from apps.authentication.services import revoke_temporary_permit

        permit = get_object_or_404(TemporaryAccessPermit, pk=pk)
        revoked = revoke_temporary_permit(request.user, permit.id, request=request)
        return Response(TemporaryAccessPermitSerializer(revoked).data)


class ChangePasswordView(APIView):
    """POST — Usuario autenticado cambia su propia contraseña (RF-001)."""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Cambiar contraseña (self-service)",
        description=(
            "RF-001 — El usuario autenticado cambia su propia contraseña proporcionando "
            "la contraseña actual y la nueva. Invalida todos los tokens JWT activos "
            "(fuerza re-login) y registra evento de auditoría."
        ),
        tags=[TAG_AUTH],
        request=ChangePasswordSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {"message": {"type": "string"}},
            },
            **standard_error_responses(include_403=False),
        },
    )
    def post(self, request):
        ser = ChangePasswordSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        change_own_password(
            request.user,
            ser.validated_data["current_password"],
            ser.validated_data["new_password"],
            request=request,
        )
        return Response({"message": "Contraseña actualizada correctamente."})


class ForgotPasswordView(APIView):
    """POST — Solicitar recuperación de contraseña por email (sin autenticación)."""

    permission_classes = (AllowAny,)

    @extend_schema(
        summary="Solicitar recuperación de contraseña",
        description=(
            "RF-001 — Envía un email con enlace de recuperación válido por 1 hora. "
            "La respuesta es siempre genérica para no revelar si el email existe (anti-enumeración)."
        ),
        tags=[TAG_AUTH],
        auth=[],
        request=ForgotPasswordSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {"message": {"type": "string"}},
            },
            **standard_error_responses(include_401=False, include_422=False),
        },
    )
    def post(self, request):
        ser = ForgotPasswordSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        request_password_reset(ser.validated_data["email"], request=request)
        return Response(
            {
                "message": (
                    "Si el correo está registrado recibirás instrucciones "
                    "para recuperar tu contraseña."
                )
            }
        )


class ResetPasswordView(APIView):
    """POST — Restablecer contraseña usando el token recibido por email."""

    permission_classes = (AllowAny,)

    @extend_schema(
        summary="Restablecer contraseña con token",
        description=(
            "RF-001 — Valida el token de recuperación (1 h de vigencia, un solo uso), "
            "cambia la contraseña e invalida todas las sesiones JWT activas."
        ),
        tags=[TAG_AUTH],
        auth=[],
        request=ResetPasswordSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {"message": {"type": "string"}},
            },
            **standard_error_responses(include_401=False),
        },
    )
    def post(self, request):
        ser = ResetPasswordSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        reset_password_with_token(
            ser.validated_data["token"],
            ser.validated_data["new_password"],
            request=request,
        )
        return Response({"message": "Contraseña restablecida correctamente."})
