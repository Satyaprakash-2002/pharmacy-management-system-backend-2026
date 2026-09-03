from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Branch
from .serializers import (
    BranchCreateSerializer,
    BranchUpdateSerializer,
    BranchStatusSerializer
)
from accounts.permissions import IsRetailerAdmin


class CreateBranchView(APIView):

    permission_classes = [IsRetailerAdmin]

    def post(self, request):

        serializer = BranchCreateSerializer(data=request.data)

        if serializer.is_valid():

            branch = serializer.save(
                retailer=request.user.retailer
            )

            return Response(
                {
                    "message": "Branch created successfully.",
                    "branch": {
                        "id": branch.id,
                        "name": branch.name,
                        "address": branch.address,
                        "phone": branch.phone,
                        "is_active": branch.is_active,
                        "retailer": {
                            "id": branch.retailer.id,
                            "name": branch.retailer.name,
                        },
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

class BranchListView(APIView):

    permission_classes = [IsRetailerAdmin]

    def get(self, request):

        branches = Branch.objects.filter(
            retailer=request.user.retailer
        )

        serializer = BranchCreateSerializer(
            branches,
            many=True
        )

        return Response(
            {
                "retailer": {
                    "id": request.user.retailer.id,
                    "name": request.user.retailer.name,
                },
                "branches": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

class BranchUpdateView(APIView):

    permission_classes = [IsRetailerAdmin]

    def put(self, request, branch_id):

        try:
            branch = Branch.objects.get(
                id=branch_id,
                retailer=request.user.retailer
            )
        except Branch.DoesNotExist:
            return Response(
                {
                    "error": "Branch not found or you do not have permission to update this branch."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BranchUpdateSerializer(
            branch,
            data=request.data
        )

        if serializer.is_valid():

            branch = serializer.save()

            return Response(
                {
                    "message": "Branch updated successfully.",
                    "branch": {
                        "id": branch.id,
                        "name": branch.name,
                        "address": branch.address,
                        "phone": branch.phone,
                        "is_active": branch.is_active,
                        "retailer": {
                            "id": branch.retailer.id,
                            "name": branch.retailer.name,
                        },
                    },
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

class BranchStatusView(APIView):

    permission_classes = [IsRetailerAdmin]

    def patch(self, request, branch_id):

        try:
            branch = Branch.objects.get(
                id=branch_id,
                retailer=request.user.retailer
            )
        except Branch.DoesNotExist:
            return Response(
                {
                    "error": "Branch not found or you do not have permission to change its status."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BranchStatusSerializer(
            branch,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            branch = serializer.save()

            return Response(
                {
                    "message": "Branch status updated successfully.",
                    "branch": {
                        "id": branch.id,
                        "name": branch.name,
                        "is_active": branch.is_active,
                    },
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )