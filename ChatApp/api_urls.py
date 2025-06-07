from django.urls import path

from .api_views import RetentionPolicyListCreateView

urlpatterns = [
    path('retention/', RetentionPolicyListCreateView.as_view(), name='retention'),
]
