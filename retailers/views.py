
from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import RetailerCreateSerializer
from rest_framework.permissions import AllowAny


class RetailerCreateView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RetailerCreateSerializer(data=request.data)

        if serializer.is_valid():
            retailer = serializer.save()

            return Response(
                {
                    "message": "Retailer and Super Admin created successfully.",
                    "retailer_id": retailer.id,
                    "retailer_name": retailer.name,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )
