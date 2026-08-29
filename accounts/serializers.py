from rest_framework import serializers
from .models import User
from retailers.models import Retailer
from branches.models import Branch


class SuperAdminCreateSerializer(serializers.ModelSerializer):
    retailer_id = serializers.IntegerField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "retailer_id",
        ]

    def create(self, validated_data):
        retailer_id = validated_data.pop("retailer_id")

        try:
            retailer = Retailer.objects.get(id=retailer_id)
        except Retailer.DoesNotExist:
            raise serializers.ValidationError(
                {"retailer_id": "Retailer does not exist."}
            )

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=User.Role.RETAILER_ADMIN,
            retailer=retailer,
            branch=None,
        )

        return user


class AdminCreateSerializer(serializers.ModelSerializer):
    branch_id = serializers.IntegerField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "branch_id",
        ]

    def create(self, validated_data):
        branch_id = validated_data.pop("branch_id")

        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            raise serializers.ValidationError(
                {"branch_id": "Branch does not exist."}
            )

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=User.Role.BRANCH_ADMIN,
            retailer=branch.retailer,
            branch=branch,
        )

        return user


class StaffUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
        ]

    def create(self, validated_data):
        creator = self.context["request"].user

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=self.context["role"],
            retailer=creator.retailer,
            branch=creator.branch,
        )

        return user