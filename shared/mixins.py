"""Mixins reutilizables para vistas DRF (extensión futura, RNF-005)."""


class ICMRoleContextMixin:
    """Adjunta contexto de rol al serializer vía get_serializer_context."""

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        request = self.request
        if request and request.user.is_authenticated:
            ctx["user_role"] = getattr(request.user, "role", None)
        return ctx
