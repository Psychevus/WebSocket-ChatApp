# Licensing utilities for enterprise features

from __future__ import annotations

import hmac
import hashlib
from functools import wraps

from django.conf import settings
from django.core.exceptions import PermissionDenied

PUBLIC_SALT = b"websocket-chatapp"

class EnterpriseFeatureDisabled(PermissionDenied):
    """Raised when an enterprise feature is accessed without a valid license."""
    pass


def validate_license(key: str) -> bool:
    """Validate the provided license key using HMAC-SHA256."""
    expected = hmac.new(PUBLIC_SALT, b"license", hashlib.sha256).hexdigest()
    valid = hmac.compare_digest(key or "", expected)
    if not valid:
        raise EnterpriseFeatureDisabled(
            "Enterprise features disabled: invalid license key"
        )
    return True


def enterprise_required(view_func):
    """Decorator that restricts access to enterprise-only views."""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        validate_license(getattr(settings, "ENTERPRISE_LICENSE_KEY", ""))
        return view_func(request, *args, **kwargs)

    return _wrapped_view
