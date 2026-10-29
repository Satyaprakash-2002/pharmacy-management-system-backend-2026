# -----------------------------------------------------------#
# Imports
# -----------------------------------------------------------#

from django.db import models
from django.utils import timezone

from retailers.models import Retailer
from branches.models import Branch


# -----------------------------------------------------------#
# Plan Model
# -----------------------------------------------------------#

class Plan(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    # Subscription Duration in Calendar Months
    duration_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Duration in calendar months for paid plans."
    )

    # Free Trial Duration in Days
    trial_duration_days = models.PositiveIntegerField(
        default=15,
        help_text="Duration in days for the Free Trial plan."
    )

    max_branches = models.PositiveIntegerField(
        default=1,
    )

    max_users = models.PositiveIntegerField()

    max_medicines = models.PositiveIntegerField()

    features = models.JSONField(
        default=list,
        blank=True,
    )

    is_trial = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # -----------------------------------------------------------#
    # String Representation
    # -----------------------------------------------------------#

    def __str__(self):
        return self.name


# -----------------------------------------------------------#
# Subscription Model
# -----------------------------------------------------------#

class Subscription(models.Model):

    # -----------------------------------------------------------#
    # Subscription Status
    # -----------------------------------------------------------#

    class Status(models.TextChoices):

        TRIAL_SELECTION = (
            "TRIAL_SELECTION",
            "Awaiting Trial Branch Selection",
        )

        ACTIVE = "ACTIVE", "Active"

        EXPIRED = "EXPIRED", "Expired"

        CANCELLED = "CANCELLED", "Cancelled"

        PENDING = "PENDING", "Pending Payment"

    # -----------------------------------------------------------#
    # Retailer and Plan
    # -----------------------------------------------------------#

    retailer = models.ForeignKey(
        Retailer,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )

    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )

    # -----------------------------------------------------------#
    # Selected Free Trial Branch
    # -----------------------------------------------------------#

    trial_branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="trial_subscriptions",
    )

    # -----------------------------------------------------------#
    # Subscription Dates
    # -----------------------------------------------------------#

    start_date = models.DateField(
        null=True,
        blank=True,
    )

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    # -----------------------------------------------------------#
    # Subscription Status Field
    # -----------------------------------------------------------#

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    # -----------------------------------------------------------#
    # Timestamps
    # -----------------------------------------------------------#

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # -----------------------------------------------------------#
    # Check Whether Subscription Is Currently Active
    # -----------------------------------------------------------#

    @property
    def is_currently_active(self):

        today = timezone.localdate()

        return (
            self.status == self.Status.ACTIVE
            and self.start_date is not None
            and self.end_date is not None
            and self.start_date <= today
            and self.end_date >= today
            and self.retailer.is_active
            and self.plan.is_active
        )

    # -----------------------------------------------------------#
    # String Representation
    # -----------------------------------------------------------#

    def __str__(self):
        return f"{self.retailer} - {self.plan}"


# -----------------------------------------------------------#
# Subscription History Model
# -----------------------------------------------------------#

class SubscriptionHistory(models.Model):

    # -----------------------------------------------------------#
    # Subscription History Actions
    # -----------------------------------------------------------#

    class Action(models.TextChoices):

        ASSIGNED = "ASSIGNED", "Plan Assigned"

        UPGRADED = "UPGRADED", "Plan Upgraded"

        DOWNGRADED = "DOWNGRADED", "Plan Downgraded"

        RENEWED = "RENEWED", "Subscription Renewed"

        TRIAL_EXTENDED = "TRIAL_EXTENDED", "Free Trial Extended"

        CANCELLED = "CANCELLED", "Subscription Cancelled"

        EXPIRED = "EXPIRED", "Subscription Expired"

    # -----------------------------------------------------------#
    # Related Subscription
    # -----------------------------------------------------------#

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="history",
    )

    # -----------------------------------------------------------#
    # Previous and New Plans
    # -----------------------------------------------------------#

    previous_plan = models.ForeignKey(
        Plan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="previous_subscription_history",
    )

    new_plan = models.ForeignKey(
        Plan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="new_subscription_history",
    )

    # -----------------------------------------------------------#
    # Previous Subscription Dates
    # -----------------------------------------------------------#

    previous_start_date = models.DateField(
        null=True,
        blank=True,
    )

    previous_end_date = models.DateField(
        null=True,
        blank=True,
    )

    # -----------------------------------------------------------#
    # New Subscription Dates
    # -----------------------------------------------------------#

    new_start_date = models.DateField(
        null=True,
        blank=True,
    )

    new_end_date = models.DateField(
        null=True,
        blank=True,
    )

    # -----------------------------------------------------------#
    # Trial Extension Details
    # -----------------------------------------------------------#

    days_extended = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    # -----------------------------------------------------------#
    # User Who Performed the Action
    # -----------------------------------------------------------#

    changed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscription_changes",
    )

    # -----------------------------------------------------------#
    # Additional Notes
    # -----------------------------------------------------------#

    notes = models.TextField(
        blank=True,
    )

    # -----------------------------------------------------------#
    # Timestamp
    # -----------------------------------------------------------#

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    # -----------------------------------------------------------#
    # String Representation
    # -----------------------------------------------------------#

    def __str__(self):
        return (
            f"{self.subscription.retailer} - "
            f"{self.get_action_display()} - "
            f"{self.created_at:%Y-%m-%d}"
        )

    # -----------------------------------------------------------#
    # Action Field
    # -----------------------------------------------------------#

    action = models.CharField(
        max_length=20,
        choices=Action.choices,
    )
