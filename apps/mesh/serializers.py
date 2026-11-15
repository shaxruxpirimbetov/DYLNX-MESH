from rest_framework import serializers
from apps.user.serializers import ResponseUserSerializer
from .models import Mesh

class MeshSerializer(serializers.ModelSerializer):
    user = ResponseUserSerializer(read_only=True)
    messages_count = serializers.IntegerField(read_only=True, required=False)
    class Meta:
        model = Mesh
        fields = "__all__"
        read_only_fields = ["qrcode", "url"]

class ActivateMeshSerializer(serializers.ModelSerializer):
    telegram_id = serializers.IntegerField(required=True)
    class Meta:
        model = Mesh
        fields = ["is_active", "phone", "telegram_id", "password", "until"]
        extra_kwargs = {"password": {"write_only": True}}
        read_only_fields = ["until"]