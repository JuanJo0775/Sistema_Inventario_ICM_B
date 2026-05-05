from django.urls import path

from apps.audit.views import AuditLogDetailView, AuditLogListView

urlpatterns = [
    path("", AuditLogListView.as_view(), name="audit-logs"),
    path("<uuid:pk>/", AuditLogDetailView.as_view(), name="audit-log-detail"),
]
