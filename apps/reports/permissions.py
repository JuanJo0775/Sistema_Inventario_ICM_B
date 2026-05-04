from rest_framework.permissions import BasePermission


class IsAdminOrAlmacenista(BasePermission):
    def has_permission(self, request, view):
        return False
