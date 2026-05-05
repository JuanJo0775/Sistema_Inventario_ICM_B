"""Serializers de autenticación (RF-001, RF-002)."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import UserRole
from apps.authentication.services import OutsideOperatingHoursError, authenticate_user, is_within_operating_hours

User = get_user_model()


def user_login_profile(user: User) -> dict:
    """Perfil público devuelto en login y documentación (RF-001, sin contraseña)."""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "phone": getattr(user, "phone", "") or "",
        "role": getattr(user, "role", ""),
        "is_active": user.is_active,
    }


class LoginRequestSerializer(serializers.Serializer):
    """Cuerpo de login: contraseña obligatoria; usuario o correo (al menos uno)."""

    username = serializers.CharField(required=False, allow_blank=True, help_text="Nombre de usuario único.")
    email = serializers.EmailField(required=False, allow_blank=True, help_text="Correo registrado (alternativa a username).")
    password = serializers.CharField(write_only=True)


class ICMTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    RF-001 — JWT con reglas ICM (BR-03 auxiliar) y login por `username` o `email`.

    No usa `super().validate()` para conservar auditoría y mensajes de dominio.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields[self.username_field] = serializers.CharField(
            write_only=True,
            required=False,
            allow_blank=True,
        )
        self.fields["email"] = serializers.EmailField(write_only=True, required=False, allow_blank=True)

    def validate(self, attrs):
        request = self.context.get("request")
        username = (attrs.get(self.username_field) or "").strip()
        email = (attrs.get("email") or "").strip()
        password = attrs["password"]

        if email and not username:
            lookup = User.objects.filter(email__iexact=email).first()
            if lookup is None:
                from apps.audit.models import AuditEventType
                from apps.audit.services import log_event

                log_event(
                    AuditEventType.LOGIN_FAILED,
                    user=None,
                    request=request,
                    username_attempted=email,
                    detail={"reason": "bad_credentials", "via": "email"},
                )
                raise AuthenticationFailed("Credenciales inválidas.")
            username = lookup.username

        if not username:
            raise serializers.ValidationError(
                {self.username_field: "Indique nombre de usuario o correo electrónico."},
                code="required",
            )

        try:
            user = authenticate_user(
                username,
                password,
                request=request,
            )
        except OutsideOperatingHoursError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        except AuthenticationFailed:
            raise

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        for token in (refresh, access):
            token["user_id"] = str(user.id)
            token["role"] = getattr(user, "role", "") or ""
            token["email"] = user.email or ""
            token["username"] = user.username

        return {
            "refresh": str(refresh),
            "access": str(access),
            "user": user_login_profile(user),
        }


class ICMTokenRefreshSerializer(TokenRefreshSerializer):
    """
    RF-001, BR-03 — Renueva access; los auxiliares solo obtienen token en franja operativa.

    Alineado a criterios Gherkin en `docs/ERS_ICM_Requisitos.md` (Feature inicio de sesión,
    Scenario 3: acceso bloqueado fuera de horario) y a `docs/ICM_Informe_Elicitacion_v2_plus.docx.md`
    (BR-03: franjas 07:00–12:00 y 14:00–17:00 para auxiliares). La renovación JWT no debe eludir esa regla.
    """

    def validate(self, attrs: dict) -> dict:
        refresh = RefreshToken(attrs["refresh"])
        user_id = refresh.get("user_id")
        if user_id is not None:
            user = User.objects.filter(pk=user_id).only("id", "role", "is_active").first()
            if user is not None and user.is_active and getattr(user, "role", None) == UserRole.AUXILIAR_DESPACHO:
                if not is_within_operating_hours():
                    raise PermissionDenied(detail="Acceso no permitido fuera del horario operativo del auxiliar de despacho.")
        return super().validate(attrs)


class UserSerializer(serializers.ModelSerializer):
    """Perfil de usuario (RF-002) — lectura y actualización parcial por almacenista."""

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
            "is_active",
            "is_staff",
            "created_by",
            "created_at",
            "updated_at",
            "last_login",
        )
        read_only_fields = ("id", "created_at", "updated_at", "last_login", "created_by", "is_staff")


class UserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField()
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(required=False, allow_blank=True, max_length=20, default="")
    role = serializers.ChoiceField(choices=UserRole.choices)

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username__iexact=value.strip()).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese nombre de usuario.")
        return value.strip()

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value.strip()).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese correo.")
        return value.strip().lower()
