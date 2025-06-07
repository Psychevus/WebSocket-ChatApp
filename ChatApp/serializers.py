from rest_framework import serializers

from ChatApp.models import RetentionPolicy


class RetentionPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = RetentionPolicy
        fields = ['id', 'scope', 'ttl_seconds', 'override_until']
