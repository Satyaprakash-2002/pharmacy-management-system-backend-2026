
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone

from rest_framework import serializers

from .models import User, PasswordSetupToken
from .utils import validate_password_setup_token
from branches.models import Branch


#-----------------------------------------------------------#
# Admin Create Serializer
#-----------------------------------------------------------#

# Creates a Branch Admin associated with a specific branch.
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

        # Retrieve the selected branch ID.
        branch_id = validated_data.pop("branch_id")

        # Validate that the branch exists.
        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            raise serializers.ValidationError(
                {"branch_id": "Branch does not exist."}
            )

        # Create the Branch Admin with a securely hashed password.
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


#-----------------------------------------------------------#
# Staff User Create Serializer
#-----------------------------------------------------------#

# Creates a staff user under the creator's retailer and branch.
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

        # Retrieve the user creating this staff account.
        creator = self.context["request"].user

        # Create the staff account.
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


#-----------------------------------------------------------#
# User Update Serializer
#-----------------------------------------------------------#

# Allows permitted user profile fields to be updated.
class UserUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
        ]


#-----------------------------------------------------------#
# Password Setup Serializer
#-----------------------------------------------------------#

# Validates the password setup token and the new password.
class PasswordSetupSerializer(serializers.Serializer):

    # Token received through the password setup link.
    token = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    # New password selected by the user.
    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    # Confirmation of the new password.
    confirm_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    # Validates the token and submitted passwords.
    def validate(self, attrs):

        # Find and validate the password setup token.
        token_record = validate_password_setup_token(
            attrs["token"]
        )

        # Reject missing, expired, or previously used tokens.
        if token_record is None:
            raise serializers.ValidationError({
                "token": (
                    "This password setup link is invalid, "
                    "expired, or already used."
                )
            })

        # Ensure both password fields match.
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "The passwords do not match."
            })

        # Apply Django's configured password validation rules.
        validate_password(
            attrs["new_password"],
            user=token_record.user,
        )

        # Store the token record for the save operation.
        attrs["token_record"] = token_record

        return attrs

    # Sets the new password and marks the token as used.
    @transaction.atomic
    def create(self, validated_data):

        # Lock the token record to help prevent concurrent reuse.
        token_record = (
            PasswordSetupToken.objects
            .select_for_update()
            .select_related("user")
            .get(pk=validated_data["token_record"].pk)
        )

        # Recheck token validity before changing the password.
        if not token_record.is_valid():
            raise serializers.ValidationError({
                "token": (
                    "This password setup link is invalid, "
                    "expired, or already used."
                )
            })

        # Set the password using Django's password hashing.
        user = token_record.user
        user.set_password(validated_data["new_password"])
        user.save(update_fields=["password"])

        # Mark the token as used to prevent reuse.
        token_record.used_at = timezone.now()
        token_record.save(update_fields=["used_at"])

        return user
