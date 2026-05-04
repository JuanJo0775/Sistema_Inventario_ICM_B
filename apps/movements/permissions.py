from rest_framework.permissions import BasePermission


class IsMovementsOperator(BasePermission):
    def has_permission(self, request, view):
        return False
