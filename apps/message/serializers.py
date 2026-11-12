from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    mesh_uuid = serializers.UUIDField(source="mesh.uuid", read_only=True)
    owner_telegram_id = serializers.CharField(source="mesh.telegram_id", read_only=True)
    is_author = serializers.BooleanField(read_only=True)
    class Meta:
        model = Message
        fields = "__all__"