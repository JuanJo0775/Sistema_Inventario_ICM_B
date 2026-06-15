"""Authenticated media file serving (ALTA-19)."""

from __future__ import annotations

import os

from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def protected_media(request, path: str):
    """Serve MEDIA_ROOT files only to authenticated users.

    In production, delegate to Nginx X-Accel-Redirect instead of this view.
    """
    full_path = os.path.join(settings.MEDIA_ROOT, path)
    # Guard against path traversal
    media_root = os.path.abspath(settings.MEDIA_ROOT)
    if (
        not os.path.abspath(full_path).startswith(media_root + os.sep)
        and os.path.abspath(full_path) != media_root
    ):
        raise Http404
    if not os.path.isfile(full_path):
        raise Http404
    return FileResponse(open(full_path, "rb"))  # noqa: WPS515
