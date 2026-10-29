from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    AdminCreateSerializer,
    StaffUserCreateSerializer,
    UserUpdateSerializer,
    PasswordSetupSerializer,
)
from .permissions import (
    IsRetailerAdmin,
    IsBranchAdmin,
    IsRetailerOrBranchAdmin,
)

from branches.models import Branch
from subscriptions.models import Subscription


#-----------------------------------------------------------#
# Password Setup View
#-----------------------------------------------------------#

class PasswordSetupView(APIView):

    # This endpoint is public because the user may not have
    # a password yet. The secure token authorizes password setup.
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):

        # Validate the token and the new password fields.
        serializer = PasswordSetupSerializer(
            data=request.data
        )

        if serializer.is_valid():

            # Set the user's password and mark the token as used.
            user = serializer.save()

            return Response(
                {
                    "message": (
                        "Password set successfully. "
                        "You can now log in using your new password."
                    ),
                    "username": user.username,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


# ----------------------------------------------------------- #
# Subscription User Limit Validation
# ----------------------------------------------------------- #

def check_user_limit(retailer):

    today = timezone.localdate()

    # Find the current active subscription
    subscription = Subscription.objects.select_related(
        "plan",
        "trial_branch",
    ).filter(
        retailer=retailer,
        status=Subscription.Status.ACTIVE,
        start_date__lte=today,
        end_date__gte=today,
        plan__is_active=True,
        retailer__is_active=True,
    ).order_by("-created_at").first()

    # Check whether a subscription exists
    if subscription is None:

        # Check whether the retailer is waiting to select a trial branch
        trial_selection_exists = Subscription.objects.filter(
            retailer=retailer,
            status=Subscription.Status.TRIAL_SELECTION,
            plan__is_trial=True,
            plan__is_active=True,
            retailer__is_active=True,
        ).exists()

        if trial_selection_exists:
            return Response(
                {
                    "error": (
                        "Your Free Trial has not started yet. "
                        "Select a branch to activate your 15-day trial."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "error": (
                    "No active subscription found. "
                    "Please activate a trial or purchase a plan."
                )
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    # A trial must have a selected branch
    if subscription.plan.is_trial and not subscription.trial_branch_id:
        return Response(
            {
                "error": "No branch has been selected for the Free Trial."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    # Count users across the entire retailer
    current_users = User.objects.filter(
        retailer=retailer
    ).count()

    # Enforce the plan's user limit
    if current_users >= subscription.plan.max_users:
        return Response(
            {
                "error": "Your plan's user limit has been reached.",
                "plan": subscription.plan.name,
                "max_users": subscription.plan.max_users,
                "current_users": current_users,
                "message": (
                    "Please upgrade your subscription "
                    "to create more users."
                ),
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    return None


# ----------------------------------------------------------- #
# Login View
# ----------------------------------------------------------- #

class LoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.select_related(
                "retailer",
                "branch",
            ).get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {"error": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"error": "User account is inactive."},
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
                "retailer_id": (
                    user.retailer_id if user.retailer_id else None
                ),
                "branch_id": (
                    user.branch_id if user.branch_id else None
                ),
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )


# ----------------------------------------------------------- #
# Create Branch Admin View
# ----------------------------------------------------------- #

class CreateAdminView(APIView):

    permission_classes = [IsRetailerAdmin]

    def post(self, request):

        branch_id = request.data.get("branch_id")

        if not branch_id:
            return Response(
                {"error": "branch_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Branch must belong to the logged-in retailer
        try:
            branch = Branch.objects.get(
                id=branch_id,
                retailer=request.user.retailer,
            )
        except (Branch.DoesNotExist, ValueError, TypeError):
            return Response(
                {
                    "error": (
                        "Branch not found or does not "
                        "belong to your retailer."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not branch.is_active:
            return Response(
                {
                    "error": "Cannot create an Admin for an inactive branch."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # During a trial, only the selected trial branch can be used
        active_subscription = Subscription.objects.filter(
            retailer=request.user.retailer,
            status=Subscription.Status.ACTIVE,
            start_date__lte=timezone.localdate(),
            end_date__gte=timezone.localdate(),
            plan__is_trial=True,
            plan__is_active=True,
            retailer__is_active=True,
        ).order_by("-created_at").first()

        if (
            active_subscription
            and active_subscription.trial_branch_id != branch.id
        ):
            return Response(
                {
                    "error": (
                        "During the Free Trial, users can only be "
                        "created for the selected trial branch."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        limit_error = check_user_limit(request.user.retailer)

        if limit_error:
            return limit_error

        serializer = AdminCreateSerializer(data=request.data)

        if serializer.is_valid():
            admin = serializer.save()

            return Response(
                {
                    "message": "Branch Admin created successfully.",
                    "admin": {
                        "id": admin.id,
                        "username": admin.username,
                        "email": admin.email,
                        "role": admin.role,
                        "retailer_id": admin.retailer_id,
                        "branch_id": admin.branch_id,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


# ----------------------------------------------------------- #
# Create Branch User View
# ----------------------------------------------------------- #

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
                    "error": (
                        "Branch Admin can create only Pharmacist, "
                        "Cashier, or Staff users."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        retailer = request.user.retailer
        branch = request.user.branch

        if retailer is None or branch is None:
            return Response(
                {"error": "Your account is not linked to a retailer and branch."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not branch.is_active:
            return Response(
                {"error": "Users cannot be created for an inactive branch."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # During a trial, only the selected branch can be used
        active_subscription = Subscription.objects.filter(
            retailer=retailer,
            status=Subscription.Status.ACTIVE,
            start_date__lte=timezone.localdate(),
            end_date__gte=timezone.localdate(),
            plan__is_trial=True,
            plan__is_active=True,
            retailer__is_active=True,
        ).order_by("-created_at").first()

        if (
            active_subscription
            and active_subscription.trial_branch_id != branch.id
        ):
            return Response(
                {
                    "error": (
                        "This branch is not selected for the Free Trial."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        limit_error = check_user_limit(retailer)

        if limit_error:
            return limit_error

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


# ----------------------------------------------------------- #
# Retailer User List View
# ----------------------------------------------------------- #

class RetailerUserListView(APIView):

    permission_classes = [IsRetailerAdmin]

    def get(self, request):

        users = User.objects.filter(
            retailer=request.user.retailer
        ).exclude(
            role=User.Role.RETAILER_ADMIN
        ).select_related("branch")

        return Response(
            {
                "retailer": request.user.retailer.name,
                "users": [
                    {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                        "branch_id": user.branch_id,
                        "branch": (
                            user.branch.name if user.branch else None
                        ),
                        "is_active": user.is_active,
                    }
                    for user in users
                ],
            },
            status=status.HTTP_200_OK,
        )


# ----------------------------------------------------------- #
# Branch User List View
# ----------------------------------------------------------- #

class BranchUserListView(APIView):

    permission_classes = [IsBranchAdmin]

    def get(self, request):

        users = User.objects.filter(
            retailer=request.user.retailer,
            branch=request.user.branch,
        ).exclude(
            role=User.Role.BRANCH_ADMIN
        )

        return Response(
            {
                "branch": request.user.branch.name,
                "users": [
                    {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                        "is_active": user.is_active,
                    }
                    for user in users
                ],
            },
            status=status.HTTP_200_OK,
        )


# ----------------------------------------------------------- #
# User Update View
# ----------------------------------------------------------- #

class UserUpdateView(APIView):

    permission_classes = [IsRetailerOrBranchAdmin]

    def put(self, request, user_id):

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Retailer Admin can update users within their retailer
        if request.user.role == User.Role.RETAILER_ADMIN:

            if user.retailer != request.user.retailer:
                return Response(
                    {"error": "You cannot update this user."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Branch Admin can update users within their branch
        elif request.user.role == User.Role.BRANCH_ADMIN:

            if (
                user.retailer != request.user.retailer
                or user.branch != request.user.branch
            ):
                return Response(
                    {"error": "You cannot update this user."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = UserUpdateSerializer(
            user,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "message": "User updated successfully.",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": user.role,
                        "retailer_id": user.retailer_id,
                        "branch_id": user.branch_id,
                    },
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )
