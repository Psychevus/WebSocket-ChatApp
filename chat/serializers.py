from rest_framework import serializers
from ChatApp.models import Message, Reaction
from django.db.models import Count


class ReactionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Reaction
        fields = ["emoji", "user"]


class MessageSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "content",
            "timestamp",
            "expires_at",
            "parent",
            "children",
            "reactions",
        ]

    def get_children(self, obj):
        queryset = obj.children.all().order_by("timestamp")
        return MessageSerializer(queryset, many=True).data

    def get_reactions(self, obj):
        qs = obj.reactions.values("emoji").annotate(count=Count("id"))
        return {r["emoji"]: r["count"] for r in qs}
