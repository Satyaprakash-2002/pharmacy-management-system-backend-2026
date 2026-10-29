
# -----------------------------------------------------------#
# Imports
# -----------------------------------------------------------#

import calendar
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from rest_framework import serializers

from .models import Retailer
from accounts.models import User
from branches.models import Branch
from subscriptions.models import Plan, Subscription, SubscriptionHistory


# -----------------------------------------------------------#
# Calculate Subscription End Date
# -----------------------------------------------------------#

def calculate_subscription_end_date(start_date, plan):
    """
    Calculate the inclusive end date.

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

    month_index = start_date.month - 1 + months

    target_year = start_date.year + month_index // 12
    target_month = month_index % 12 + 1

    target_day = min(
        start_date.day,
        calendar.monthrange(target_year, target_month)[1],
    )

    anniversary_date = start_date.replace(
        year=target_year,
        month=target_month,
        day=target_day,
    )

    # End date is inclusive.
    return anniversary_date - timedelta(days=1)


# -----------------------------------------------------------#
# Retailer Registration Serializer
# -----------------------------------------------------------#

class RetailerCreateSerializer(serializers.ModelSerializer):

    admin_username = serializers.CharField(write_only=True)

    admin_email = serializers.EmailField(write_only=True)

    admin_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    admin_first_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    admin_last_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.filter(is_active=True),
        write_only=True,
    )

    class Meta:
        model = Retailer

        fields = [
            "name",
            "admin_username",
            "admin_email",
            "admin_password",
            "admin_first_name",
            "admin_last_name",
            "plan_id",
        ]

    # -----------------------------------------------------------#
    # Validate Selected Plan
    # -----------------------------------------------------------#

    def validate_plan_id(self, plan):

        if plan.is_trial:

            if plan.price != 0:
                raise serializers.ValidationError(
                    "The Free Trial must cost ₹0."
                )

            if plan.trial_duration_days != 15:
                raise serializers.ValidationError(
                    "The Free Trial must last exactly 15 days."
                )

            if plan.duration_months is not None:
                raise serializers.ValidationError(
                    "The Free Trial must use days, not months."
                )

        else:

            allowed_durations = {
                "Basic": 1,
                "Standard": 3,
                "Pro": 12,
            }

            if plan.name not in allowed_durations:
                raise serializers.ValidationError(
                    "Select Free Trial, Basic, Standard, or Pro."
                )

            if plan.duration_months != allowed_durations[plan.name]:
                raise serializers.ValidationError(
                    f"{plan.name} must have a duration of "
                    f"{allowed_durations[plan.name]} month(s)."
                )

        return plan

    # -----------------------------------------------------------#
    # Create Retailer, Admin, Branch and Subscription
    # -----------------------------------------------------------#

    @transaction.atomic
    def create(self, validated_data):

        # -----------------------------------------------------------#
        # Extract Admin and Plan Details
        # -----------------------------------------------------------#

        admin_username = validated_data.pop("admin_username")
        admin_email = validated_data.pop("admin_email")
        admin_password = validated_data.pop("admin_password")

        admin_first_name = validated_data.pop(
            "admin_first_name",
            "",
        )

        admin_last_name = validated_data.pop(
            "admin_last_name",
            "",
        )

        plan = validated_data.pop("plan_id")

        # -----------------------------------------------------------#
        # Create Retailer
        # -----------------------------------------------------------#

        retailer = Retailer.objects.create(**validated_data)

        # -----------------------------------------------------------#
        # Create Retailer Admin
        # -----------------------------------------------------------#

        retailer_admin = User.objects.create_user(
            username=admin_username,
            email=admin_email,
            password=admin_password,
            first_name=admin_first_name,
            last_name=admin_last_name,
            role=User.Role.RETAILER_ADMIN,
            retailer=retailer,
            branch=None,
        )

        # -----------------------------------------------------------#
        # Create Default Branch
        # -----------------------------------------------------------#

        default_branch = Branch.objects.create(
            retailer=retailer,
            name="Main Branch",
            is_active=True,
        )

        # -----------------------------------------------------------#
        # Calculate Subscription Dates
        # -----------------------------------------------------------#

        start_date = timezone.localdate()

        end_date = calculate_subscription_end_date(
            start_date,
            plan,
        )

        # -----------------------------------------------------------#
        # Assign Selected Plan to Retailer
        # -----------------------------------------------------------#

        subscription_data = {
            "retailer": retailer,
            "plan": plan,
            "start_date": start_date,
            "end_date": end_date,
            "status": Subscription.Status.ACTIVE,
        }

        # During the Free Trial, only Main Branch is permitted.
        if plan.is_trial:
            subscription_data["trial_branch"] = default_branch
        else:
            subscription_data["trial_branch"] = None

        subscription = Subscription.objects.create(
            **subscription_data
        )

        # -----------------------------------------------------------#
        # Create Initial Subscription History
        # -----------------------------------------------------------#

        SubscriptionHistory.objects.create(
            subscription=subscription,
            previous_plan=None,
            new_plan=plan,
            previous_start_date=None,
            previous_end_date=None,
            new_start_date=start_date,
            new_end_date=end_date,
            changed_by=self.context["request"].user,
            action=SubscriptionHistory.Action.ASSIGNED,
            notes="Initial subscription assigned during retailer creation.",
        )

        # -----------------------------------------------------------#
        # Return Created Objects
        # -----------------------------------------------------------#

        return {
            "retailer": retailer,
            "super_admin": retailer_admin,
            "default_branch": default_branch,
            "subscription": subscription,
        }
