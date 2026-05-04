from rest_framework.permissions import BasePermission


class IsInventoryOperator(BasePermission):
    def has_permission(self, request, view):
        return False
