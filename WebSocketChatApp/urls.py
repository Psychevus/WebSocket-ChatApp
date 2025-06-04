from django.contrib import admin
from django.urls import path, include
from ChatApp import views as chat_views

urlpatterns = [
    path('admin/audit-logs/', chat_views.audit_logs_view, name='audit_logs'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('saml2/', include('djangosaml2.urls')),
    path('scim/v2/', include('django_scim.urls')),
    path('', include('ChatApp.urls')),

]
