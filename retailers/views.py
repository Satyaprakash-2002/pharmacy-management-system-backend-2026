from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import RetailerCreateSerializer
from accounts.permissions import IsPlatformOwner


class RetailerCreateView(APIView):

    permission_classes = [IsPlatformOwner]

    def post(self, request):

        serializer = RetailerCreateSerializer(data=request.data)

        if serializer.is_valid():

            result = serializer.save()

            retailer = result["retailer"]
            super_admin = result["super_admin"]
            default_branch = result["default_branch"]

            return Response(
                {
                    "message": "Retailer, Super Admin and default branch created successfully.",

                    "retailer": {
                        "id": retailer.id,
                        "name": retailer.name,
                    },

                    "super_admin": {
                        "id": super_admin.id,
                        "username": super_admin.username,
                        "email": super_admin.email,
                        "role": super_admin.role,
                    },

                    "default_branch": {
                        "id": default_branch.id,
                        "name": default_branch.name,
                        "address": default_branch.address,
                        "phone": default_branch.phone,
                        "is_active": default_branch.is_active,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )