from rest_framework import serializers
from .models import User


# Serializer used to display user information.
# This is mainly used when returning user data through APIs.
class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User

        # Fields that can be returned through the API.
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "retailer",
            "branch",
        ]


# Serializer used when creating a new user.
# This handles registration/user creation.
class UserRegistrationSerializer(serializers.ModelSerializer):

    # Password is accepted when creating a user,
    # but it will never be returned in the API response.
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    class Meta:
        model = User

        fields = [
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "role",
            "retailer",
            "branch",
        ]

    # Creates the user and securely hashes the password.
    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(**validated_data)

        # Hash the password before saving it.
        user.set_password(password)

        user.save()

        return user