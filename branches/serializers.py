from rest_framework import serializers
from .models import Branch


class BranchCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Branch
        fields = [
            "id",
            "name",
            "address",
            "phone",
            "is_active",
        ]
        read_only_fields = [
            "id",
            "is_active",
        ]


class BranchUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Branch
        fields = [
            "name",
            "address",
            "phone",
        ]

class BranchStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = Branch
        fields = [
            "is_active",
        ]