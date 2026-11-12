from rest_framework import serializers
from apps.user.serializers import ResponseUserSerializer
from .models import Mesh

class MeshSerializer(serializers.ModelSerializer):
    user = ResponseUserSerializer(read_only=True)
    class Meta:
        model = Mesh
        fields = "__all__"


class ChangeAllPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mesh
        fields = ["password"]