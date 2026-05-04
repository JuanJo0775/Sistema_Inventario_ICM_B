from rest_framework.permissions import BasePermission


class IsAlertManager(BasePermission):
    def has_permission(self, request, view):
        return False
