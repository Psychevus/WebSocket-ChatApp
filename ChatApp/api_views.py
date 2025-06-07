from rest_framework import generics, permissions, views
from rest_framework.response import Response
from django.db.models import Q

from ChatApp.models import RetentionPolicy, Conversation, Message, MessageReceipt
from ChatApp.serializers import RetentionPolicySerializer


class RetentionPolicyListCreateView(generics.ListCreateAPIView):
    queryset = RetentionPolicy.objects.all()
    serializer_class = RetentionPolicySerializer
    permission_classes = [permissions.IsAdminUser]


class ReceiptView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = []
        conversations = Conversation.objects.filter(Q(user1=request.user) | Q(user2=request.user))
        for c in conversations:
            last_seen = 0
            try:
                receipt = MessageReceipt.objects.get(user=request.user, conversation=c)
                last_seen = receipt.last_seen_id
            except MessageReceipt.DoesNotExist:
                pass
            unread = Message.objects.filter(conversation=c, id__gt=last_seen).count()
            data.append({"conversation_id": c.id, "unread": unread})
        return Response(data)
