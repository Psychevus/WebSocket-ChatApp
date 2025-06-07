from django.contrib import admin
from django.urls import path, include
from django.conf import settings

from ChatApp import views as chat_views
from chat.licensing import (
    enterprise_required,
    validate_license,
    EnterpriseFeatureDisabled,
)

urlpatterns = [
    path('admin/audit-logs/', chat_views.audit_logs_view, name='audit_logs'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
]

# Gate enterprise features
def _license_error(request, *args, **kwargs):
    raise EnterpriseFeatureDisabled()

try:
    validate_license(settings.ENTERPRISE_LICENSE_KEY)
    urlpatterns += [
        path('saml2/', include('djangosaml2.urls')),
        path('scim/v2/', include('django_scim.urls')),
    ]
except EnterpriseFeatureDisabled:
    urlpatterns += [
        path('saml2/', enterprise_required(_license_error)),
        path('scim/v2/', enterprise_required(_license_error)),
    ]

urlpatterns += [
    path('', include('ChatApp.urls')),
]
