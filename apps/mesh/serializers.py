from rest_framework import serializers
from apps.user.serializers import ResponseUserSerializer
from .models import Mesh

class MeshSerializer(serializers.ModelSerializer):
    user = ResponseUserSerializer(read_only=True)
    class Meta:
        model = Mesh
        fields = "__all__"

class ActivateMeshSerializer(serializers.ModelSerializer):
    telegram_id = serializers.IntegerField(required=True)
    class Meta:
        model = Mesh
        fields = ["is_active", "phone", "telegram_id"]