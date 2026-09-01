# from django.shortcuts import render

# # Create your views here.
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status

# from .models import User
# from .serializers import (
#     SuperAdminCreateSerializer,
#     AdminCreateSerializer,
#     StaffUserCreateSerializer,
# )
# from .permissions import (
#     IsPlatformOwner,
#     IsRetailerAdmin,
#     IsBranchAdmin,
# )


# class CreateSuperAdminView(APIView):

#     permission_classes = [IsPlatformOwner]

#     def post(self, request):

#         serializer = SuperAdminCreateSerializer(data=request.data)

#         if serializer.is_valid():
#             user = serializer.save()

#             return Response(
#                 {
#                     "message": "Super Admin created successfully.",
#                     "user_id": user.id,
#                     "username": user.username,
#                     "role": user.role,
#                     "retailer": user.retailer.name,
#                 },
#                 status=status.HTTP_201_CREATED,
#             )

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST,
#         )


# class CreateAdminView(APIView):

#     permission_classes = [IsRetailerAdmin]

#     def post(self, request):

#         branch_id = request.data.get("branch_id")

#         if not branch_id:
#             return Response(
#                 {"error": "branch_id is required."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # Check whether branch belongs to logged-in Super Admin's retailer
#         from branches.models import Branch

#         try:
#             branch = Branch.objects.get(
#                 id=branch_id,
#                 retailer=request.user.retailer
#             )
#         except Branch.DoesNotExist:
#             return Response(
#                 {
#                     "error": "You cannot assign Admin to this branch."
#                 },
#                 status=status.HTTP_403_FORBIDDEN,
#             )

#         serializer = AdminCreateSerializer(data=request.data)

#         if serializer.is_valid():
#             user = serializer.save()

#             return Response(
#                 {
#                     "message": "Admin created successfully.",
#                     "user_id": user.id,
#                     "username": user.username,
#                     "role": user.role,
#                     "retailer": user.retailer.name,
#                     "branch": user.branch.name,
#                 },
#                 status=status.HTTP_201_CREATED,
#             )

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST,
#         )


# class CreateBranchUserView(APIView):

#     permission_classes = [IsBranchAdmin]

#     def post(self, request):

#         role = request.data.get("role")

#         allowed_roles = [
#             User.Role.PHARMACIST,
#             User.Role.CASHIER,
#             User.Role.STAFF,
#         ]

#         if role not in allowed_roles:
#             return Response(
#                 {
#                     "error": "Admin can create only Pharmacist, Cashier or Staff."
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         serializer = StaffUserCreateSerializer(
#             data=request.data,
#             context={
#                 "request": request,
#                 "role": role,
#             },
#         )

#         if serializer.is_valid():
#             user = serializer.save()

#             return Response(
#                 {
#                     "message": f"{role} created successfully.",
#                     "user_id": user.id,
#                     "username": user.username,
#                     "role": user.role,
#                     "retailer": user.retailer.name,
#                     "branch": user.branch.name,
#                 },
#                 status=status.HTTP_201_CREATED,
#             )

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST,
#         )

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    SuperAdminCreateSerializer,
    AdminCreateSerializer,
    StaffUserCreateSerializer,
)
from .permissions import (
    IsPlatformOwner,
    IsRetailerAdmin,
    IsBranchAdmin,
)


class LoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        username = request.data.get("username")
        password = request.data.get("password")

        # Check username and password
        if not username or not password:
            return Response(
                {
                    "error": "Username and password are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Find user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {
                    "error": "Invalid username or password."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Check password
        if not user.check_password(password):
            return Response(
                {
                    "error": "Invalid username or password."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Check active status
        if not user.is_active:
            return Response(
                {
                    "error": "User account is inactive."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful.",
                "user_id": user.id,
                "username": user.username,
                "role": user.role,
                "retailer_id": user.retailer.id if user.retailer else None,
                "branch_id": user.branch.id if user.branch else None,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )


class CreateSuperAdminView(APIView):

    permission_classes = [IsPlatformOwner]

    def post(self, request):

        serializer = SuperAdminCreateSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "message": "Super Admin created successfully.",
                    "user_id": user.id,
                    "username": user.username,
                    "role": user.role,
                    "retailer": user.retailer.name,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class CreateAdminView(APIView):

    permission_classes = [IsRetailerAdmin]

    def post(self, request):

        branch_id = request.data.get("branch_id")

        if not branch_id:
            return Response(
                {
                    "error": "branch_id is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        from branches.models import Branch

        try:
            branch = Branch.objects.get(
                id=branch_id,
                retailer=request.user.retailer
            )
        except Branch.DoesNotExist:
            return Response(
                {
                    "error": "You cannot assign Admin to this branch."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AdminCreateSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "message": "Admin created successfully.",
                    "user_id": user.id,
                    "username": user.username,
                    "role": user.role,
                    "retailer": user.retailer.name,
                    "branch": user.branch.name,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class CreateBranchUserView(APIView):

    permission_classes = [IsBranchAdmin]

    def post(self, request):

        role = request.data.get("role")

        allowed_roles = [
            User.Role.PHARMACIST,
            User.Role.CASHIER,
            User.Role.STAFF,
        ]

        if role not in allowed_roles:
            return Response(
                {
                    "error": "Admin can create only Pharmacist, Cashier or Staff."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = StaffUserCreateSerializer(
            data=request.data,
            context={
                "request": request,
                "role": role,
            },
        )

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "message": f"{role} created successfully.",
                    "user_id": user.id,
                    "username": user.username,
                    "role": user.role,
                    "retailer": user.retailer.name,
                    "branch": user.branch.name,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )