
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

from django.conf import settings
from django.core.mail import send_mail

from accounts.utils import generate_password_setup_token


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
# Send Retailer Welcome Email
# -----------------------------------------------------------#

def send_retailer_welcome_email(
    retailer,
    retailer_admin,
    default_branch,
    subscription,
    raw_token,
):

    # Build the password setup URL using the frontend URL.
    frontend_url = getattr(
        settings,
        "FRONTEND_URL",
        "http://localhost:3000",
    ).rstrip("/")

    password_setup_url = (
        f"{frontend_url}/set-password/{raw_token}"
    )

    plan = subscription.plan

    # Find the other active plans available for upgrades.
    available_plans = Plan.objects.filter(
        is_active=True,
        is_trial=False,
    ).exclude(
        id=plan.id,
    ).order_by("price")

    # Prepare the upgrade plan details.
    upgrade_details = []

    for upgrade_plan in available_plans:

        upgrade_details.append(
            f"""
{upgrade_plan.name}

Price: ₹{upgrade_plan.price:.2f}
Duration: {upgrade_plan.duration_months} month(s)
Users Allowed: {upgrade_plan.max_users}
Branches Allowed: {upgrade_plan.max_branches}
Medicines Allowed: {upgrade_plan.max_medicines}
"""
        )

    if not upgrade_details:
        upgrade_text = "No other paid plans are currently available."
    else:
        upgrade_text = "\n".join(upgrade_details)

    # Format trial and paid plan duration.
    if plan.is_trial:
        plan_type = "Free Trial"
        duration_text = f"{plan.trial_duration_days} days"
        billing_cycle = "Trial"
    else:
        plan_type = "Paid"
        duration_text = f"{plan.duration_months} month(s)"
        billing_cycle = "Monthly" if plan.duration_months == 1 else "Multi-month"

    # Build the welcome email.
    subject = "Welcome to Pharmacy ERP - Your Account Details"

    message = f"""
Hello {retailer_admin.first_name or retailer_admin.username},

Your retailer account has been created successfully.

RETAILER DETAILS
================

Retailer Name: {retailer.name}
Username: {retailer_admin.username}
Email: {retailer_admin.email}

BRANCH DETAILS
==============

Branch Name: {default_branch.name}
Branch ID: {default_branch.id}

CURRENT SUBSCRIPTION DETAILS
============================

Plan Name: {plan.name}
Plan Type: {plan_type}
Price: ₹{plan.price:.2f}
Duration: {duration_text}
Max Users: {plan.max_users}
Max Branches: {plan.max_branches}
Max Medicines: {plan.max_medicines}

SUBSCRIPTION INFORMATION
========================

Start Date: {subscription.start_date}
Expiry Date: {subscription.end_date}
Status: {subscription.status}
Billing Cycle: {billing_cycle}

SET YOUR PASSWORD
=================

Set your password using the secure link below:

{password_setup_url}

This link will expire in 24 hours and can only be used once.

AVAILABLE UPGRADE PLANS
=======================

{upgrade_text}

For subscription upgrades, renewals, or technical support,
please contact the Platform Support Team.

Regards,
Pharmacy ERP Team
"""

    # Send the email using the configured Django email backend.
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[retailer_admin.email],
        fail_silently=False,
    )


# -----------------------------------------------------------#
# Retailer Registration Serializer
# -----------------------------------------------------------#

class RetailerCreateSerializer(serializers.ModelSerializer):

    admin_username = serializers.CharField(write_only=True)

    admin_email = serializers.EmailField(write_only=True)

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
            password=None,
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
        # Generate Password Setup Token
        # -----------------------------------------------------------#

        raw_token = generate_password_setup_token(
            retailer_admin
        )

        # -----------------------------------------------------------#
        # Send Welcome Email After Database Commit
        # -----------------------------------------------------------#

        transaction.on_commit(
            lambda: send_retailer_welcome_email(
                retailer=retailer,
                retailer_admin=retailer_admin,
                default_branch=default_branch,
                subscription=subscription,
                raw_token=raw_token,
            )
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
