from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.authentication.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = list(DjangoUserAdmin.fieldsets or []) + [
        ("ICM", {"fields": ("role", "created_by", "phone")}),
    ]
    list_display = ("username", "email", "role", "is_active", "is_staff")
