from django.urls import path

from .api_views import (
    RetentionPolicyListCreateView,
    ReceiptView,
    UnreadView,
    EraseUserDataView,
)

urlpatterns = [
    path('retention/', RetentionPolicyListCreateView.as_view(), name='retention'),
    path('receipts/', ReceiptView.as_view(), name='receipts'),
    path('unread/', UnreadView.as_view(), name='unread'),
    path('gdpr/erase/', EraseUserDataView.as_view(), name='gdpr-erase'),
]
