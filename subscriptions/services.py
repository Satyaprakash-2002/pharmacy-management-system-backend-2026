
# from django.db import transaction
# from django.utils import timezone

# from .models import Subscription, SubscriptionHistory


# #-----------------------------------------------------------#
# # Subscription Expiry Checking Service
# #-----------------------------------------------------------#

# @transaction.atomic
# def expire_subscriptions():

#     today = timezone.localdate()

#     expired_subscriptions = Subscription.objects.select_for_update().filter(
#         status=Subscription.Status.ACTIVE,
#         end_date__lt=today,
#     )

#     updated_count = 0

#     for subscription in expired_subscriptions:

#         #-----------------------------------------------------------#
#         # Create Subscription Expiry History
#         #-----------------------------------------------------------#

#         SubscriptionHistory.objects.create(
#             subscription=subscription,
#             previous_plan=subscription.plan,
#             new_plan=subscription.plan,
#             previous_start_date=subscription.start_date,
#             previous_end_date=subscription.end_date,
#             new_start_date=subscription.start_date,
#             new_end_date=subscription.end_date,
#             action=SubscriptionHistory.Action.EXPIRED,
#             notes="Subscription automatically expired because its expiry date has passed.",
#         )

#         #-----------------------------------------------------------#
#         # Update Subscription Status
#         #-----------------------------------------------------------#

#         subscription.status = Subscription.Status.EXPIRED

#         subscription.save(update_fields=["status", "updated_at"])

#         updated_count += 1

#     return updated_count


# -----------------------------------------------------------#
# Imports
# -----------------------------------------------------------#

from django.db import transaction
from django.utils import timezone

from .models import Subscription, SubscriptionHistory
from notifications.services import process_subscription_notifications


# -----------------------------------------------------------#
# Subscription Expiry Checking Service
# -----------------------------------------------------------#

def expire_subscriptions():

    # -----------------------------------------------------------#
    # Process Subscription Notifications
    # -----------------------------------------------------------#

    process_subscription_notifications()

    # -----------------------------------------------------------#
    # Find Expired Subscriptions
    # -----------------------------------------------------------#

    today = timezone.localdate()

    expired_subscriptions = Subscription.objects.filter(
        status=Subscription.Status.ACTIVE,
        end_date__lt=today,
    )

    updated_count = 0

    # -----------------------------------------------------------#
    # Update Expired Subscriptions
    # -----------------------------------------------------------#

    with transaction.atomic():

        expired_subscriptions = expired_subscriptions.select_for_update()

        for subscription in expired_subscriptions:

            # -----------------------------------------------------------#
            # Create Subscription Expiry History
            # -----------------------------------------------------------#

            SubscriptionHistory.objects.create(
                subscription=subscription,
                previous_plan=subscription.plan,
                new_plan=subscription.plan,
                previous_start_date=subscription.start_date,
                previous_end_date=subscription.end_date,
                new_start_date=subscription.start_date,
                new_end_date=subscription.end_date,
                action=SubscriptionHistory.Action.EXPIRED,
                notes=(
                    "Subscription automatically expired because "
                    "its expiry date has passed."
                ),
            )

            # -----------------------------------------------------------#
            # Update Subscription Status
            # -----------------------------------------------------------#

            subscription.status = Subscription.Status.EXPIRED

            subscription.save(
                update_fields=["status", "updated_at"]
            )

            updated_count += 1

    return updated_count
