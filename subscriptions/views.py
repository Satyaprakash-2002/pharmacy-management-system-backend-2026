
#-----------------------------------------------------------#
# Imports
#-----------------------------------------------------------#

import calendar
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsPlatformOwner
from branches.models import Branch

from .models import Plan, Subscription, SubscriptionHistory
from .serializers import (
    PlanSerializer,
    PlanStatusSerializer,
    SubscriptionSerializer,
)


#-----------------------------------------------------------#
# Subscription Date Helper
#-----------------------------------------------------------#

def calculate_subscription_end_date(start_date, plan):
    """
    Calculate the inclusive subscription end date.

    Free Trial: 15 days.
    Paid plans: Calendar months.
    """

    if plan.is_trial:
        return start_date + timedelta(
            days=plan.trial_duration_days - 1
        )

    months = plan.duration_months

    if months is None or months <= 0:
        raise ValueError(
            "Paid plans must have a valid duration in months."
        )

    # Calculate the target year and month.
    month_index = start_date.month - 1 + months

    target_year = start_date.year + month_index // 12
    target_month = month_index % 12 + 1

    # Handle dates such as January 31 when the target month
    # has fewer days, such as February.
    target_day = min(
        start_date.day,
        calendar.monthrange(target_year, target_month)[1],
    )

    anniversary_date = start_date.replace(
        year=target_year,
        month=target_month,
        day=target_day,
    )

    # The subscription end date is inclusive.
    return anniversary_date - timedelta(days=1)


#-----------------------------------------------------------#
# Plan List and Create
#-----------------------------------------------------------#

class PlanListCreateView(generics.ListCreateAPIView):

    serializer_class = PlanSerializer

    def get_queryset(self):
        queryset = Plan.objects.all().order_by("price")

        if not (
            self.request.user.is_authenticated
            and self.request.user.role == "PLATFORM_OWNER"
        ):
            queryset = queryset.filter(is_active=True)

        return queryset

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsPlatformOwner()]

        return [IsAuthenticated()]


#-----------------------------------------------------------#
# Plan Detail
#-----------------------------------------------------------#

class PlanDetailView(generics.RetrieveUpdateAPIView):

    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [IsPlatformOwner]


#-----------------------------------------------------------#
# Plan Status
#-----------------------------------------------------------#

class PlanStatusView(generics.UpdateAPIView):

    queryset = Plan.objects.all()
    serializer_class = PlanStatusSerializer
    permission_classes = [IsPlatformOwner]

    http_method_names = ["patch", "options", "head"]


#-----------------------------------------------------------#
# Subscription List and Create
#-----------------------------------------------------------#

class SubscriptionListCreateView(generics.ListCreateAPIView):

    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        queryset = Subscription.objects.select_related(
            "retailer",
            "plan",
            "trial_branch",
        )

        if user.role == "PLATFORM_OWNER":
            return queryset

        if user.role == "RETAILER_ADMIN":
            if user.retailer_id is None:
                return queryset.none()

            return queryset.filter(
                retailer_id=user.retailer_id
            )

        return queryset.none()


#-----------------------------------------------------------#
# Subscription Detail
#-----------------------------------------------------------#

class SubscriptionDetailView(generics.RetrieveAPIView):

    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        queryset = Subscription.objects.select_related(
            "retailer",
            "plan",
            "trial_branch",
        )

        if user.role == "PLATFORM_OWNER":
            return queryset

        if user.role == "RETAILER_ADMIN":
            if user.retailer_id is None:
                return queryset.none()

            return queryset.filter(
                retailer_id=user.retailer_id
            )

        return queryset.none()



#-----------------------------------------------------------#
# Assign, Upgrade, or Downgrade Subscription Plan
#-----------------------------------------------------------#

class ChangeSubscriptionPlanView(APIView):

    permission_classes = [IsPlatformOwner]

    @transaction.atomic
    def post(self, request):

        #-----------------------------------------------------------#
        # Validate Request Data
        #-----------------------------------------------------------#

        retailer_id = request.data.get("retailer_id")
        plan_id = request.data.get("plan_id")
        notes = request.data.get("notes", "")

        if not retailer_id or not plan_id:
            return Response(
                {
                    "error": (
                        "Both retailer_id and plan_id are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            retailer_id = int(retailer_id)
            plan_id = int(plan_id)
        except (TypeError, ValueError):
            return Response(
                {
                    "error": (
                        "retailer_id and plan_id must be valid IDs."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        #-----------------------------------------------------------#
        # Find Retailer and Selected Plan
        #-----------------------------------------------------------#

        from retailers.models import Retailer

        retailer = Retailer.objects.filter(
            id=retailer_id,
        ).first()

        if retailer is None:
            return Response(
                {"error": "Retailer not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not retailer.is_active:
            return Response(
                {"error": "This retailer is inactive."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        plan = Plan.objects.filter(
            id=plan_id,
            is_active=True,
        ).first()

        if plan is None:
            return Response(
                {"error": "The selected plan does not exist or is inactive."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # This endpoint handles paid plans only.
        # Free Trial activation and extension are separate workflows.
        if plan.is_trial:
            return Response(
                {
                    "error": (
                        "Use the dedicated Free Trial workflow "
                        "for trial subscriptions."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_durations = {
            "Basic": 1,
            "Standard": 3,
            "Pro": 12,
        }

        if plan.name not in allowed_durations:
            return Response(
                {
                    "error": (
                        "Select Basic, Standard, or Pro."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if plan.duration_months != allowed_durations[plan.name]:
            return Response(
                {
                    "error": (
                        f"{plan.name} must have a duration of "
                        f"{allowed_durations[plan.name]} month(s)."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if plan.price <= 0:
            return Response(
                {"error": "Paid plans must have a price greater than ₹0."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        #-----------------------------------------------------------#
        # Lock and Find the Current Active Subscription
        #-----------------------------------------------------------#

        today = timezone.localdate()

        current_subscription = (
            Subscription.objects.select_for_update()
            .select_related("plan", "retailer")
            .filter(
                retailer_id=retailer.id,
                status=Subscription.Status.ACTIVE,
                start_date__lte=today,
                end_date__gte=today,
            )
            .order_by("-end_date")
            .first()
        )

        # Prevent duplicate scheduled subscriptions.
        existing_pending = Subscription.objects.filter(
            retailer_id=retailer.id,
            status=Subscription.Status.PENDING,
            start_date__gt=today,
        ).exists()

        if existing_pending:
            return Response(
                {
                    "error": (
                        "This retailer already has a scheduled "
                        "subscription. Resolve that subscription "
                        "before scheduling another plan."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        #-----------------------------------------------------------#
        # Calculate New Subscription Dates
        #-----------------------------------------------------------#

        if (
            current_subscription is not None
            and current_subscription.end_date is not None
        ):
            # Preserve the current subscription until its expiry.
            new_start_date = (
                current_subscription.end_date + timedelta(days=1)
            )
        else:
            # No currently active subscription: start today.
            new_start_date = today

        new_end_date = calculate_subscription_end_date(
            new_start_date,
            plan,
        )

        if new_start_date > today:
            new_status = Subscription.Status.PENDING
        else:
            new_status = Subscription.Status.ACTIVE

        #-----------------------------------------------------------#
        # Determine History Action
        #-----------------------------------------------------------#

        previous_plan = (
            current_subscription.plan
            if current_subscription is not None
            else None
        )

        if previous_plan is None:
            action = SubscriptionHistory.Action.ASSIGNED
        elif plan.price > previous_plan.price:
            action = SubscriptionHistory.Action.UPGRADED
        elif plan.price < previous_plan.price:
            action = SubscriptionHistory.Action.DOWNGRADED
        else:
            action = SubscriptionHistory.Action.ASSIGNED

        #-----------------------------------------------------------#
        # Create New Subscription
        #-----------------------------------------------------------#

        new_subscription = Subscription.objects.create(
            retailer=retailer,
            plan=plan,
            start_date=new_start_date,
            end_date=new_end_date,
            status=new_status,
        )

        #-----------------------------------------------------------#
        # Record Subscription History
        #-----------------------------------------------------------#

        SubscriptionHistory.objects.create(
            subscription=new_subscription,
            previous_plan=previous_plan,
            new_plan=plan,
            previous_start_date=(
                current_subscription.start_date
                if current_subscription is not None
                else None
            ),
            previous_end_date=(
                current_subscription.end_date
                if current_subscription is not None
                else None
            ),
            new_start_date=new_start_date,
            new_end_date=new_end_date,
            changed_by=request.user,
            notes=notes,
            action=action,
        )

        #-----------------------------------------------------------#
        # Return Response
        #-----------------------------------------------------------#

        return Response(
            {
                "message": (
                    "Subscription plan scheduled successfully."
                    if new_status == Subscription.Status.PENDING
                    else "Subscription plan assigned successfully."
                ),
                "subscription_id": new_subscription.id,
                "retailer_id": retailer.id,
                "previous_plan": (
                    previous_plan.name
                    if previous_plan is not None
                    else None
                ),
                "new_plan": plan.name,
                "start_date": new_start_date,
                "end_date": new_end_date,
                "status": new_status,
                "history_action": action,
            },
            status=(
                status.HTTP_201_CREATED
            ),
        )



#-----------------------------------------------------------#
# Select Branch and Activate Free Trial
#-----------------------------------------------------------#

class TrialBranchSelectionView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        user = request.user

        #-----------------------------------------------------------#
        # Validate Retailer Admin
        #-----------------------------------------------------------#

        if (
            user.role != "RETAILER_ADMIN"
            or user.retailer_id is None
        ):
            return Response(
                {
                    "error": (
                        "Only a Retailer Admin can select "
                        "the Free Trial branch."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        #-----------------------------------------------------------#
        # Validate Branch ID
        #-----------------------------------------------------------#

        branch_id = request.data.get("branch_id")

        if branch_id is None:
            return Response(
                {"branch_id": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            branch_id = int(branch_id)
        except (TypeError, ValueError):
            return Response(
                {"branch_id": "Enter a valid branch ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        #-----------------------------------------------------------#
        # Find Branch Belonging to This Retailer
        #-----------------------------------------------------------#

        branch = Branch.objects.filter(
            id=branch_id,
            retailer_id=user.retailer_id,
            is_active=True,
        ).first()

        if branch is None:
            return Response(
                {
                    "branch_id": (
                        "The selected branch does not exist, "
                        "is inactive, or does not belong "
                        "to your retailer."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        #-----------------------------------------------------------#
        # Find Trial Awaiting Branch Selection
        #-----------------------------------------------------------#

        subscription = (
            Subscription.objects.select_for_update()
            .select_related("plan", "retailer")
            .filter(
                retailer_id=user.retailer_id,
                status=Subscription.Status.TRIAL_SELECTION,
                plan__is_trial=True,
            )
            .first()
        )

        if subscription is None:
            return Response(
                {
                    "error": (
                        "No Free Trial is awaiting branch selection. "
                        "The trial may already have been selected "
                        "or this retailer may have used its trial."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        #-----------------------------------------------------------#
        # Validate Trial Plan and Retailer
        #-----------------------------------------------------------#

        if (
            not subscription.plan.is_active
            or not subscription.retailer.is_active
        ):
            return Response(
                {
                    "error": (
                        "The trial plan or retailer is inactive."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            subscription.plan.price != 0
            or subscription.plan.trial_duration_days != 15
        ):
            return Response(
                {
                    "error": (
                        "The Free Trial must be free "
                        "and last exactly 15 days."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        #-----------------------------------------------------------#
        # Enforce One Trial Branch
        #-----------------------------------------------------------#

        active_branches = Branch.objects.filter(
            retailer_id=user.retailer_id,
            is_active=True,
        ).count()

        if active_branches > 1:
            return Response(
                {
                    "error": (
                        "The Free Trial supports only one active "
                        "branch. Keep only the intended trial branch "
                        "active before selecting it."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        #-----------------------------------------------------------#
        # Activate the 15-Day Trial
        #-----------------------------------------------------------#

        start_date = timezone.localdate()

        end_date = calculate_subscription_end_date(
            start_date,
            subscription.plan,
        )

        subscription.trial_branch = branch
        subscription.start_date = start_date
        subscription.end_date = end_date
        subscription.status = Subscription.Status.ACTIVE

        subscription.save(
            update_fields=[
                "trial_branch",
                "start_date",
                "end_date",
                "status",
                "updated_at",
            ]
        )

        #-----------------------------------------------------------#
        # Return Activated Trial Details
        #-----------------------------------------------------------#

        return Response(
            {
                "message": "Free Trial activated successfully.",
                "subscription_id": subscription.id,
                "retailer_id": subscription.retailer_id,
                "plan": subscription.plan.name,
                "trial_branch": {
                    "id": branch.id,
                    "name": branch.name,
                },
                "start_date": subscription.start_date,
                "end_date": subscription.end_date,
                "status": subscription.status,
            },
            status=status.HTTP_200_OK,
        )
