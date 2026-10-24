from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction

from .models import Profile


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    fullName = serializers.CharField(write_only=True)
    company = serializers.CharField(write_only=True)
    inn = serializers.CharField(write_only=True)
    phone = serializers.CharField(write_only=True)

    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    class Meta:
        model = User
        fields = (
            "id",
            "fullName",
            "email",
            "password",
            "company",
            "inn",
            "phone",
        )
        read_only_fields = ("id",)

    @transaction.atomic
    def create(self, validated_data):
        full_name = validated_data.pop("fullName")
        company = validated_data.pop("company")
        inn = validated_data.pop("inn")
        phone = validated_data.pop("phone")

        parts = full_name.strip().split(maxsplit=1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

        email = validated_data["email"]

        user = User.objects.create_user(
            username=email,
            first_name=first_name,
            last_name=last_name,
            **validated_data,
        )

        Profile.objects.create(
            user=user,
            company_name=company,
            inn=inn,
            phone=phone,
        )

        return user

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "email": instance.email,
            "fullName": instance.get_full_name(),
        } # TODO: Обработать дубликат email и проверить существование при регистрации и ошибки в будущем мб надо систематизировать

class MeSerializer(serializers.ModelSerializer):
    fullName = serializers.CharField(
        source="get_full_name",
        read_only=True,
    )
    role = serializers.CharField(
        source="profile.role",
        read_only=True,
    )
    company = serializers.CharField(
        source="profile.company_name",
        read_only=True,
    )
    inn = serializers.CharField(
        source="profile.inn",
        read_only=True,
    )
    phone = serializers.CharField(
        source="profile.phone",
        read_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "fullName",
            "role",
            "company",
            "inn",
            "phone",
        ]