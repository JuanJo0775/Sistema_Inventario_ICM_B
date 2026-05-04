"""Serializers de autenticación (RF-001, RF-002)."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import UserRole
from apps.authentication.services import OutsideOperatingHoursError, authenticate_user

User = get_user_model()


class ICMTokenObtainPairSerializer(TokenObtainPairSerializer):
    """RF-001 — Emite JWT validando reglas ICM (incluye BR-03 para auxiliares)."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = getattr(user, "role", "")
        return token

    def validate(self, attrs):
        request = self.context.get("request")
        try:
            user = authenticate_user(
                attrs["username"],
                attrs["password"],
                request=request,
            )
        except OutsideOperatingHoursError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        if user is None:
            raise AuthenticationFailed()
        refresh = RefreshToken.for_user(user)
        refresh["role"] = getattr(user, "role", "")
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {"id": user.id, "username": user.username, "role": user.role},
        }
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class UserCreateSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=UserRole.choices)
