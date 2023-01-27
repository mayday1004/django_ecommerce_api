from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from djoser.serializers import (
    UserCreateSerializer as BaseUserCreateSerializer,
    UserSerializer as BaseUserSerializer,
)


class UserCreateSerializer(BaseUserCreateSerializer):
    confirm_password = serializers.CharField(
        style={"input_type": "password"}, write_only=True
    )

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Password do not match.")
        data.pop("confirm_password")
        return data

    class Meta(BaseUserCreateSerializer.Meta):
        fields = [
            "id",
            "username",
            "password",
            "confirm_password",
            "email",
            "phone_number",
            "first_name",
            "last_name",
        ]


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ["id", "username", "password", "email", "phone_number"]

    email = serializers.EmailField(read_only=True)

    def update(self, instance, validated_data):
        validated_data["password"] = make_password(validated_data.get("password"))
        return super().update(instance, validated_data)
