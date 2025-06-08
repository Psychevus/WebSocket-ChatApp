from rest_framework import generics, permissions, views
from rest_framework.response import Response
from django.db.models import Q

from ChatApp.models import (
    RetentionPolicy,
    Conversation,
    Message,
    MessageReceipt,
)
from ChatApp.serializers import RetentionPolicySerializer
from ChatApp.tasks import erase_user_data


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


class UnreadView(views.APIView):
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


class EraseUserDataView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        confirm = request.data.get("confirm")
        if confirm != request.user.email:
            return Response({"detail": "Email confirmation mismatch."}, status=400)

        request.user.pending_erasure = True
        request.user.save(update_fields=["pending_erasure"])
        erase_user_data.apply_async((request.user.id,), countdown=30 * 24 * 60 * 60)
        return Response({"status": "scheduled"})
