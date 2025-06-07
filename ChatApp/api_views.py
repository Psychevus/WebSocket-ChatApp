from rest_framework import generics, permissions

from ChatApp.models import RetentionPolicy
from ChatApp.serializers import RetentionPolicySerializer


class RetentionPolicyListCreateView(generics.ListCreateAPIView):
    queryset = RetentionPolicy.objects.all()
    serializer_class = RetentionPolicySerializer
    permission_classes = [permissions.IsAdminUser]
