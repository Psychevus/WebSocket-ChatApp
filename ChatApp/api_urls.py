from django.urls import path

from .api_views import (
    RetentionPolicyListCreateView,
    ReceiptView,
    EraseUserDataView,
)

urlpatterns = [
    path('retention/', RetentionPolicyListCreateView.as_view(), name='retention'),
    path('receipts/', ReceiptView.as_view(), name='receipts'),
    path('gdpr/erase/', EraseUserDataView.as_view(), name='gdpr-erase'),
]
