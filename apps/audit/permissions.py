from rest_framework.permissions import BasePermission


class IsAuditViewer(BasePermission):
    def has_permission(self, request, view):
        return False
