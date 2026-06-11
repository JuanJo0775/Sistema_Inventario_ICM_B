"""Serializers de autenticación (RF-001, RF-002)."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import UserRole
from apps.authentication.services import OutsideOperatingHoursError, authenticate_user

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

    username = serializers.CharField(
        required=False, allow_blank=True, help_text="Nombre de usuario único."
    )
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text="Correo registrado (alternativa a username).",
    )
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
        self.fields["email"] = serializers.EmailField(
            write_only=True, required=False, allow_blank=True
        )

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
                {
                    self.username_field: "Indique nombre de usuario o correo electrónico."
                },
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

    Alineado a criterios Gherkin en `docs/requisitos/ERS_ICM_Requisitos.md` (Feature inicio de sesión,
    Scenario 3: acceso bloqueado fuera de horario) y a `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md`
    (BR-03: franjas 07:00–12:00 y 14:00–17:00 para auxiliares). La renovación JWT no debe eludir esa regla.
    """

    def validate(self, attrs: dict) -> dict:
        refresh = RefreshToken(attrs["refresh"])
        user_id = refresh.get("user_id")
        if user_id is not None:
            user = (
                User.objects.filter(pk=user_id).only("id", "role", "is_active").first()
            )
            if (
                user is not None
                and user.is_active
                and getattr(user, "role", None) == UserRole.AUXILIAR_DESPACHO
            ):
                from apps.authentication.selectors import check_user_access

                if not check_user_access(user):
                    raise PermissionDenied(
                        detail="Acceso no permitido fuera del horario operativo del auxiliar de despacho."
                    )
        return super().validate(attrs)


class UserSerializer(serializers.ModelSerializer):
    """Perfil de usuario (RF-002) — lectura y actualización parcial por almacenista."""

    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True, allow_null=True
    )

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
            "created_by_username",
            "created_at",
            "updated_at",
            "last_login",
        )
        read_only_fields = (
            "id",
            "is_active",
            "created_at",
            "updated_at",
            "last_login",
            "created_by",
            "created_by_username",
            "is_staff",
        )


class UserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField()
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(
        required=False, allow_blank=True, max_length=20, default=""
    )
    role = serializers.ChoiceField(choices=UserRole.choices)

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username__iexact=value.strip()).exists():
            raise serializers.ValidationError(
                "Ya existe un usuario con ese nombre de usuario."
            )
        return value.strip()

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value.strip()).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese correo.")
        return value.strip().lower()


class UserScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        from apps.authentication.models import UserSchedule

        model = UserSchedule
        fields = (
            "id",
            "user",
            "morning_start",
            "morning_end",
            "afternoon_start",
            "afternoon_end",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "created_at", "updated_at")

    def validate(self, attrs):
        morning_start = attrs.get(
            "morning_start", self.instance.morning_start if self.instance else None
        )
        morning_end = attrs.get(
            "morning_end", self.instance.morning_end if self.instance else None
        )
        afternoon_start = attrs.get(
            "afternoon_start",
            self.instance.afternoon_start if self.instance else None,
        )
        afternoon_end = attrs.get(
            "afternoon_end", self.instance.afternoon_end if self.instance else None
        )

        if (morning_start and not morning_end) or (not morning_start and morning_end):
            raise serializers.ValidationError(
                "Debe especificar inicio y fin de la franja de la mañana."
            )
        if (afternoon_start and not afternoon_end) or (
            not afternoon_start and afternoon_end
        ):
            raise serializers.ValidationError(
                "Debe especificar inicio y fin de la franja de la tarde."
            )

        if morning_start and morning_end and morning_start >= morning_end:
            raise serializers.ValidationError(
                "La hora de inicio de la mañana debe ser anterior a la de fin."
            )
        if afternoon_start and afternoon_end and afternoon_start >= afternoon_end:
            raise serializers.ValidationError(
                "La hora de inicio de la tarde debe ser anterior a la de fin."
            )

        return attrs


class TemporaryAccessPermitSerializer(serializers.ModelSerializer):
    granted_by_username = serializers.CharField(
        source="granted_by.username", read_only=True
    )
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        from apps.authentication.models import TemporaryAccessPermit

        model = TemporaryAccessPermit
        fields = (
            "id",
            "user",
            "user_username",
            "start_datetime",
            "end_datetime",
            "allow_24_7",
            "custom_morning_start",
            "custom_morning_end",
            "custom_afternoon_start",
            "custom_afternoon_end",
            "reason",
            "granted_by",
            "granted_by_username",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "granted_by", "created_at", "updated_at")

    def validate(self, attrs):
        start_datetime = attrs.get(
            "start_datetime", self.instance.start_datetime if self.instance else None
        )
        end_datetime = attrs.get(
            "end_datetime", self.instance.end_datetime if self.instance else None
        )
        allow_24_7 = attrs.get(
            "allow_24_7", self.instance.allow_24_7 if self.instance else False
        )
        custom_morning_start = attrs.get(
            "custom_morning_start",
            self.instance.custom_morning_start if self.instance else None,
        )
        custom_morning_end = attrs.get(
            "custom_morning_end",
            self.instance.custom_morning_end if self.instance else None,
        )
        custom_afternoon_start = attrs.get(
            "custom_afternoon_start",
            self.instance.custom_afternoon_start if self.instance else None,
        )
        custom_afternoon_end = attrs.get(
            "custom_afternoon_end",
            self.instance.custom_afternoon_end if self.instance else None,
        )
        reason = attrs.get("reason", self.instance.reason if self.instance else "")

        if start_datetime and end_datetime and start_datetime >= end_datetime:
            raise serializers.ValidationError(
                "La fecha/hora de fin debe ser posterior a la de inicio."
            )

        if not reason or not reason.strip():
            raise serializers.ValidationError(
                "El motivo de la autorización es obligatorio."
            )

        if not allow_24_7:
            has_morning = custom_morning_start and custom_morning_end
            has_afternoon = custom_afternoon_start and custom_afternoon_end
            if not has_morning and not has_afternoon:
                raise serializers.ValidationError(
                    "Si no se permite acceso 24/7, debe configurar al menos una franja horaria válida (mañana o tarde)."
                )

        if (custom_morning_start and not custom_morning_end) or (
            not custom_morning_start and custom_morning_end
        ):
            raise serializers.ValidationError(
                "Debe especificar inicio y fin de la franja custom de la mañana."
            )
        if (custom_afternoon_start and not custom_afternoon_end) or (
            not custom_afternoon_start and custom_afternoon_end
        ):
            raise serializers.ValidationError(
                "Debe especificar inicio y fin de la franja custom de la tarde."
            )

        if (
            custom_morning_start
            and custom_morning_end
            and custom_morning_start >= custom_morning_end
        ):
            raise serializers.ValidationError(
                "La hora de inicio de la mañana debe ser anterior a la de fin."
            )
        if (
            custom_afternoon_start
            and custom_afternoon_end
            and custom_afternoon_start >= custom_afternoon_end
        ):
            raise serializers.ValidationError(
                "La hora de inicio de la tarde debe ser anterior a la de fin."
            )

        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Cambio de contraseña self-service (RF-001)."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Las contraseñas no coinciden."}
            )
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    """Solicitud de recuperación de contraseña por email (RF-001)."""

    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    """Restablecimiento de contraseña con token de recuperación (RF-001)."""

    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Las contraseñas no coinciden."}
            )
        return attrs
