
#-----------------------------------------------------------#
# Imports
#-----------------------------------------------------------#

from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Branch
from .serializers import (
    BranchCreateSerializer,
    BranchUpdateSerializer,
    BranchStatusSerializer,
)

from subscriptions.models import Subscription
from accounts.permissions import IsRetailerAdmin


#-----------------------------------------------------------#
# Get Current Active Subscription
#-----------------------------------------------------------#

def get_current_subscription(retailer):

    today = timezone.localdate()

    return (
        Subscription.objects.select_related("plan")
        .filter(
            retailer=retailer,
            status=Subscription.Status.ACTIVE,
            start_date__lte=today,
            end_date__gte=today,
            plan__is_active=True,
            retailer__is_active=True,
        )
        .order_by("-created_at")
        .first()
    )


#-----------------------------------------------------------#
# Get Subscription Awaiting Trial Selection
#-----------------------------------------------------------#

def get_trial_selection_subscription(retailer):

    return (
        Subscription.objects.select_related("plan")
        .filter(
            retailer=retailer,
            status=Subscription.Status.TRIAL_SELECTION,
            plan__is_trial=True,
            plan__is_active=True,
        )
        .order_by("-created_at")
        .first()
    )


#-----------------------------------------------------------#
# Create Branch
#-----------------------------------------------------------#

class CreateBranchView(APIView):

    permission_classes = [IsRetailerAdmin]

    def post(self, request):

        retailer = request.user.retailer

        #-----------------------------------------------------------#
        # Validate Retailer
        #-----------------------------------------------------------#

        if retailer is None:
            return Response(
                {"error": "Your account is not linked to a retailer."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not retailer.is_active:
            return Response(
                {"error": "Your retailer account is inactive."},
                status=status.HTTP_403_FORBIDDEN,
            )

        #-----------------------------------------------------------#
        # Check Subscription State
        #-----------------------------------------------------------#

        subscription = get_current_subscription(retailer)
        trial_selection = get_trial_selection_subscription(retailer)

        # Allow branch setup before the trial starts.
        # Branch limits will be enforced after trial selection.
        if trial_selection is not None:
            serializer = BranchCreateSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            branch = serializer.save(retailer=retailer)

            return Response(
                {
                    "message": (
                        "Branch created successfully. Select one branch "
                        "to activate your 15-day Free Trial."
                    ),
                    "branch": {
                        "id": branch.id,
                        "name": branch.name,
                        "address": branch.address,
                        "phone": branch.phone,
                        "is_active": branch.is_active,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        #-----------------------------------------------------------#
        # Require an Active Subscription
        #-----------------------------------------------------------#

        if subscription is None:
            return Response(
                {
                    "error": (
                        "You do not have an active subscription or a "
                        "Free Trial awaiting branch selection. "
                        "Please activate a trial or obtain a paid plan."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        #-----------------------------------------------------------#
        # Prevent Additional Branches During the Trial
        #-----------------------------------------------------------#

        if subscription.plan.is_trial:
            return Response(
                {
                    "error": (
                        "Additional branches cannot be created during "
                        "the Free Trial. Upgrade to a paid plan first."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        #-----------------------------------------------------------#
        # Enforce Paid Plan Branch Limit
        #-----------------------------------------------------------#

        active_branch_count = Branch.objects.filter(
            retailer=retailer,
            is_active=True,
        ).count()

        if active_branch_count >= subscription.plan.max_branches:
            return Response(
                {
                    "error": "Your subscription branch limit has been reached.",
                    "branch_limit": subscription.plan.max_branches,
                    "active_branches": active_branch_count,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        #-----------------------------------------------------------#
        # Validate Branch Data
        #-----------------------------------------------------------#

        serializer = BranchCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        #-----------------------------------------------------------#
        # Save New Branch
        #-----------------------------------------------------------#

        branch = serializer.save(retailer=retailer)

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
                        "id": retailer.id,
                        "name": retailer.name,
                    },
                },
            },
            status=status.HTTP_201_CREATED,
        )


#-----------------------------------------------------------#
# List Retailer's Branches
#-----------------------------------------------------------#

class BranchListView(APIView):

    permission_classes = [IsRetailerAdmin]

    def get(self, request):

        retailer = request.user.retailer

        if retailer is None:
            return Response(
                {"error": "Your account is not linked to a retailer."},
                status=status.HTTP_403_FORBIDDEN,
            )

        branches = Branch.objects.filter(retailer=retailer)

        serializer = BranchCreateSerializer(branches, many=True)

        return Response(
            {
                "retailer": {
                    "id": retailer.id,
                    "name": retailer.name,
                },
                "branches": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


#-----------------------------------------------------------#
# Update Branch Details
#-----------------------------------------------------------#

class BranchUpdateView(APIView):

    permission_classes = [IsRetailerAdmin]

    def put(self, request, branch_id):

        retailer = request.user.retailer

        if retailer is None:
            return Response(
                {"error": "Your account is not linked to a retailer."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            branch = Branch.objects.get(
                id=branch_id,
                retailer=retailer,
            )
        except Branch.DoesNotExist:
            return Response(
                {
                    "error": (
                        "Branch not found or you do not have "
                        "permission to update this branch."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BranchUpdateSerializer(
            branch,
            data=request.data,
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

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


#-----------------------------------------------------------#
# Update Branch Active Status
#-----------------------------------------------------------#

class BranchStatusView(APIView):

    permission_classes = [IsRetailerAdmin]

    def patch(self, request, branch_id):

        retailer = request.user.retailer

        if retailer is None:
            return Response(
                {"error": "Your account is not linked to a retailer."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            branch = Branch.objects.get(
                id=branch_id,
                retailer=retailer,
            )
        except Branch.DoesNotExist:
            return Response(
                {
                    "error": (
                        "Branch not found or you do not have "
                        "permission to change its status."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BranchStatusSerializer(
            branch,
            data=request.data,
            partial=True,
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        requested_is_active = serializer.validated_data.get(
            "is_active",
            branch.is_active,
        )

        #-----------------------------------------------------------#
        # Check Restrictions When Activating a Branch
        #-----------------------------------------------------------#

        if requested_is_active and not branch.is_active:

            subscription = get_current_subscription(retailer)
            trial_selection = get_trial_selection_subscription(retailer)

            # During setup, branches may be prepared for trial selection.
            if trial_selection is not None:
                branch = serializer.save()

                return Response(
                    {
                        "message": (
                            "Branch activated for setup. Select one "
                            "branch to start the Free Trial."
                        ),
                        "branch": {
                            "id": branch.id,
                            "name": branch.name,
                            "is_active": branch.is_active,
                        },
                    },
                    status=status.HTTP_200_OK,
                )

            if subscription is None:
                return Response(
                    {
                        "error": (
                            "You do not have an active subscription. "
                            "Please activate a trial or obtain a paid plan."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # During a trial, only its assigned branch may be active.
            if subscription.plan.is_trial:
                if subscription.trial_branch_id != branch.id:
                    return Response(
                        {
                            "error": (
                                "During the Free Trial, only the "
                                "assigned trial branch can be activated."
                            )
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

            # Enforce branch limits for paid subscriptions.
            active_branch_count = Branch.objects.filter(
                retailer=retailer,
                is_active=True,
            ).exclude(id=branch.id).count()

            if active_branch_count >= subscription.plan.max_branches:
                return Response(
                    {
                        "error": "Your subscription branch limit has been reached.",
                        "branch_limit": subscription.plan.max_branches,
                        "active_branches": active_branch_count,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        #-----------------------------------------------------------#
        # Save Branch Status
        #-----------------------------------------------------------#

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
