from rest_framework.permissions import BasePermission


class IsAlmacenistaOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return False
