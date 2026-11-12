from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        groups = validated_data.pop("groups", None)
        perms = validated_data.pop("user_permissions", None)
        user = User.objects.create_user(**validated_data)
        if groups is not None:
            user.groups.set(groups)
        if perms is not None:
            user.user_permissions.set(perms)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save(update_fields=["password"])
        return instance

class ResponseUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username"]