
#-----------------------------------------------------------#
# Imports
#-----------------------------------------------------------#

from rest_framework import serializers

from .models import Plan, Subscription, SubscriptionHistory


#-----------------------------------------------------------#
# Plan Management
#-----------------------------------------------------------#

class PlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = Plan

        fields = [
            "id",
            "name",
            "price",
            "duration_months",
            "trial_duration_days",
            "max_branches",
            "max_users",
            "max_medicines",
            "features",
            "is_trial",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    #-----------------------------------------------------------#
    # Validate Plan Details
    #-----------------------------------------------------------#

    def validate(self, attrs):

        price = attrs.get(
            "price",
            getattr(self.instance, "price", None),
        )

        duration_months = attrs.get(
            "duration_months",
            getattr(self.instance, "duration_months", None),
        )

        trial_duration_days = attrs.get(
            "trial_duration_days",
            getattr(self.instance, "trial_duration_days", 15),
        )

        is_trial = attrs.get(
            "is_trial",
            getattr(self.instance, "is_trial", False),
        )

        name = attrs.get(
            "name",
            getattr(self.instance, "name", None),
        )

        if price is not None and price < 0:
            raise serializers.ValidationError({
                "price": "Price cannot be negative."
            })

        if is_trial:

            if price != 0:
                raise serializers.ValidationError({
                    "price": "The Free Trial must cost ₹0."
                })

            if trial_duration_days != 15:
                raise serializers.ValidationError({
                    "trial_duration_days": (
                        "The Free Trial must last exactly 15 days."
                    )
                })

        else:

            if duration_months is None or duration_months <= 0:
                raise serializers.ValidationError({
                    "duration_months": (
                        "Paid plans must have a duration "
                        "of at least one month."
                    )
                })

            allowed_durations = {
                "Basic": 1,
                "Standard": 3,
                "Pro": 12,
            }

            if name in allowed_durations:
                if duration_months != allowed_durations[name]:
                    raise serializers.ValidationError({
                        "duration_months": (
                            f"{name} must have a duration of "
                            f"{allowed_durations[name]} month(s)."
                        )
                    })

        if is_trial and self.instance is not None:
            if self.instance.subscriptions.exists():
                if not self.instance.is_trial:
                    raise serializers.ValidationError({
                        "is_trial": (
                            "A plan already used by subscriptions "
                            "cannot be changed to a Free Trial."
                        )
                    })

        return attrs


#-----------------------------------------------------------#
# Plan Status Management
#-----------------------------------------------------------#

class PlanStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = Plan

        fields = [
            "id",
            "is_active",
        ]

        read_only_fields = [
            "id",
        ]


#-----------------------------------------------------------#
# Subscription Management
#-----------------------------------------------------------#

class SubscriptionSerializer(serializers.ModelSerializer):

    retailer_name = serializers.CharField(
        source="retailer.name",
        read_only=True,
    )

    plan_name = serializers.CharField(
        source="plan.name",
        read_only=True,
    )

    is_currently_active = serializers.BooleanField(
        read_only=True,
    )

    trial_branch = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

    class Meta:
        model = Subscription

        fields = [
            "id",
            "retailer",
            "retailer_name",
            "plan",
            "plan_name",
            "trial_branch",
            "start_date",
            "end_date",
            "status",
            "is_currently_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "trial_branch",
            "start_date",
            "end_date",
            "status",
            "created_at",
            "updated_at",
        ]

    #-----------------------------------------------------------#
    # Validate Subscription Details
    #-----------------------------------------------------------#

    def validate(self, attrs):

        request = self.context.get("request")

        if request is None:
            raise serializers.ValidationError(
                "Request context is required."
            )

        user = request.user

        retailer = attrs.get(
            "retailer",
            getattr(self.instance, "retailer", None),
        )

        plan = attrs.get(
            "plan",
            getattr(self.instance, "plan", None),
        )

        if user.role != "PLATFORM_OWNER":
            raise serializers.ValidationError(
                "Only the Platform Owner can manage subscriptions."
            )

        if retailer is None:
            raise serializers.ValidationError({
                "retailer": "A retailer is required."
            })

        if plan is None:
            raise serializers.ValidationError({
                "plan": "A plan is required."
            })

        if not retailer.is_active:
            raise serializers.ValidationError({
                "retailer": "This retailer is inactive."
            })

        if not plan.is_active:
            raise serializers.ValidationError({
                "plan": "This plan is inactive."
            })

        if plan.is_trial:

            if (
                plan.price != 0
                or plan.trial_duration_days != 15
            ):
                raise serializers.ValidationError({
                    "plan": (
                        "The Free Trial must cost ₹0 "
                        "and last 15 days."
                    )
                })

        else:

            allowed_durations = {
                "Basic": 1,
                "Standard": 3,
                "Pro": 12,
            }

            if plan.name not in allowed_durations:
                raise serializers.ValidationError({
                    "plan": (
                        "Select Free Trial, Basic, Standard, or Pro."
                    )
                })

            if plan.duration_months != allowed_durations[plan.name]:
                raise serializers.ValidationError({
                    "plan": (
                        f"{plan.name} must have a duration of "
                        f"{allowed_durations[plan.name]} month(s)."
                    )
                })

        return attrs

    #-----------------------------------------------------------#
    # Subscription Creation
    #-----------------------------------------------------------#

    def create(self, validated_data):

        raise serializers.ValidationError(
            "Use the dedicated Platform Owner workflow to assign "
            "plans, upgrade subscriptions, renew subscriptions, "
            "or extend Free Trials."
        )


#-----------------------------------------------------------#
# Subscription History Management
#-----------------------------------------------------------#

class SubscriptionHistorySerializer(serializers.ModelSerializer):

    action_display = serializers.CharField(
        source="get_action_display",
        read_only=True,
    )

    retailer_name = serializers.CharField(
        source="subscription.retailer.name",
        read_only=True,
    )

    previous_plan_name = serializers.CharField(
        source="previous_plan.name",
        read_only=True,
        allow_null=True,
    )

    new_plan_name = serializers.CharField(
        source="new_plan.name",
        read_only=True,
        allow_null=True,
    )

    changed_by_username = serializers.CharField(
        source="changed_by.username",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = SubscriptionHistory

        fields = [
            "id",
            "subscription",
            "retailer_name",
            "action",
            "action_display",
            "previous_plan",
            "previous_plan_name",
            "new_plan",
            "new_plan_name",
            "previous_start_date",
            "previous_end_date",
            "new_start_date",
            "new_end_date",
            "days_extended",
            "changed_by",
            "changed_by_username",
            "notes",
            "created_at",
        ]

        read_only_fields = fields
