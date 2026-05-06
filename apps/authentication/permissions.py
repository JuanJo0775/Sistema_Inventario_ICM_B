from rest_framework.permissions import BasePermission


class IsAlmacenista(BasePermission):
    def has_permission(self, request, view):
        return False


class IsAuxiliarDespacho(BasePermission):
    def has_permission(self, request, view):
        return False

