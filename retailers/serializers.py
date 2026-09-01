
from django.db import transaction
from rest_framework import serializers

from .models import Retailer
from accounts.models import User


class RetailerCreateSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(write_only=True)
    admin_email = serializers.EmailField(write_only=True)
    admin_password = serializers.CharField(write_only=True)
    admin_first_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True
    )
    admin_last_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True
    )

    class Meta:
        model = Retailer
        fields = [
            "name",
            "admin_username",
            "admin_email",
            "admin_password",
            "admin_first_name",
            "admin_last_name",
        ]

    @transaction.atomic
    def create(self, validated_data):

        admin_username = validated_data.pop("admin_username")
        admin_email = validated_data.pop("admin_email")
        admin_password = validated_data.pop("admin_password")
        admin_first_name = validated_data.pop("admin_first_name", "")
        admin_last_name = validated_data.pop("admin_last_name", "")

        # Create Retailer
        retailer = Retailer.objects.create(**validated_data)

        # Automatically create Super Admin
        User.objects.create_user(
            username=admin_username,
            email=admin_email,
            password=admin_password,
            first_name=admin_first_name,
            last_name=admin_last_name,
            role=User.Role.RETAILER_ADMIN,
            retailer=retailer,
            branch=None,
        )

        return retailer
