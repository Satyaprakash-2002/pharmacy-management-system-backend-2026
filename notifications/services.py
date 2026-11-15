
#-----------------------------------------------------------#
# Imports
#-----------------------------------------------------------#

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from subscriptions.models import Subscription
from .models import Notification, SubscriptionEmailLog


#-----------------------------------------------------------#
# Get Platform Owners
#-----------------------------------------------------------#

def get_platform_owners():

    return User.objects.filter(
        role=User.Role.PLATFORM_OWNER,
        is_active=True,
    )


#-----------------------------------------------------------#
# Get Retailer Admin
#-----------------------------------------------------------#

def get_retailer_admin(subscription):

    return User.objects.filter(
        retailer=subscription.retailer,
        role=User.Role.RETAILER_ADMIN,
        is_active=True,
    ).exclude(
        email=""
    ).order_by("id").first()


#-----------------------------------------------------------#
# Create Dashboard Notifications
#-----------------------------------------------------------#

def create_subscription_notifications(
    subscription,
    notification_type,
    title,
    message,
):

    created_notifications = []

    for owner in get_platform_owners().distinct():

        event_key = (
            f"subscription-{subscription.id}-"
            f"{notification_type}-{owner.id}"
        )

        notification, created = Notification.objects.get_or_create(
            event_key=event_key,
            defaults={
                "recipient": owner,
                "subscription": subscription,
                "title": title,
                "message": message,
                "notification_type": notification_type,
            },
        )

        if created:
            created_notifications.append(notification)

    return created_notifications



#-----------------------------------------------------------#
# Send Subscription Email
#-----------------------------------------------------------#

def send_subscription_email(
    subscription,
    notification_type,
    subject,
    message,
):

    retailer_admin = get_retailer_admin(subscription)

    if not retailer_admin:
        return False

    #-----------------------------------------------------------#
    # Generate Unique Email Event Key
    #-----------------------------------------------------------#

    event_key = (
        f"subscription-{subscription.id}-"
        f"{notification_type}"
    )

    #-----------------------------------------------------------#
    # Create Or Get Email Log
    #-----------------------------------------------------------#

    with transaction.atomic():

        email_log, created = SubscriptionEmailLog.objects.get_or_create(
            event_key=event_key,
            defaults={
                "subscription": subscription,
                "notification_type": notification_type,
                "recipient_email": retailer_admin.email,
            },
        )

        email_log = SubscriptionEmailLog.objects.select_for_update().get(
            id=email_log.id
        )

        #-----------------------------------------------------------#
        # Prevent Duplicate Emails
        #-----------------------------------------------------------#

        if email_log.email_sent:
            return True

        #-----------------------------------------------------------#
        # Send Email
        #-----------------------------------------------------------#

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email_log.recipient_email],
            fail_silently=False,
        )

        #-----------------------------------------------------------#
        # Update Email Status
        #-----------------------------------------------------------#

        email_log.email_sent = True
        email_log.sent_at = timezone.now()

        email_log.save(
            update_fields=[
                "email_sent",
                "sent_at",
            ]
        )

    return True



#-----------------------------------------------------------#
# Process Subscription Expiry Notifications
#-----------------------------------------------------------#

def process_subscription_notifications():

    today = timezone.localdate()

    subscriptions = Subscription.objects.filter(
        status=Subscription.Status.ACTIVE,
        end_date__isnull=False,
    ).select_related(
        "retailer",
        "plan",
    )

    processed_count = 0

    for subscription in subscriptions:

        expiry_date = subscription.end_date
        retailer_name = subscription.retailer.name
        is_trial = subscription.plan.is_trial

        #-----------------------------------------------------------#
        # Seven-Day Expiry Reminder
        #-----------------------------------------------------------#

        if expiry_date == today + timedelta(days=7):

            if is_trial:
                title = "Free Trial Ending in 7 Days"

                message = (
                    f"The free trial for {retailer_name} "
                    f"will end in 7 days, on {expiry_date}. "
                    "Please contact the ERP Team to purchase "
                    "a subscription plan."
                )

                email_subject = (
                    "Pharmacy ERP - Free Trial Ending in 7 Days"
                )

                email_message = (
                    f"Hello,\n\n"
                    f"Your free trial for {retailer_name} "
                    f"will end in 7 days, on {expiry_date}.\n\n"
                    "To continue using Pharmacy ERP without "
                    "interruption, please contact the ERP Team "
                    "to purchase a subscription plan.\n\n"
                    "Regards,\nPharmacy ERP Team"
                )

            else:
                title = "Subscription Expiring in 7 Days"

                message = (
                    f"The subscription for {retailer_name} "
                    f"will expire on {expiry_date}. "
                    "Please contact the retailer regarding renewal."
                )

                email_subject = (
                    "Pharmacy ERP - Subscription Expires in 7 Days"
                )

                email_message = (
                    f"Hello,\n\n"
                    f"The subscription for {retailer_name} "
                    f"will expire in 7 days, on {expiry_date}.\n\n"
                    "Please renew your subscription before it expires "
                    "to avoid interruption.\n\n"
                    "Regards,\nPharmacy ERP Team"
                )

            with transaction.atomic():

                create_subscription_notifications(
                    subscription,
                    Notification.NotificationType.SUBSCRIPTION_EXPIRING,
                    title,
                    message,
                )

                send_subscription_email(
                    subscription,
                    Notification.NotificationType.SUBSCRIPTION_EXPIRING,
                    email_subject,
                    email_message,
                )

            processed_count += 1

        #-----------------------------------------------------------#
        # Expiry-Day Notification
        #-----------------------------------------------------------#

        if expiry_date == today:

            if is_trial:
                title = "Free Trial Expires Today"

                message = (
                    f"The free trial for {retailer_name} "
                    f"expires today, {expiry_date}. "
                    "Please contact the ERP Team to purchase "
                    "a subscription plan."
                )

                email_subject = (
                    "Pharmacy ERP - Free Trial Expires Today"
                )

                email_message = (
                    f"Hello,\n\n"
                    f"Your free trial for {retailer_name} "
                    f"expires today, {expiry_date}.\n\n"
                    "To continue using Pharmacy ERP, please "
                    "contact the ERP Team to purchase "
                    "a subscription plan.\n\n"
                    "Regards,\nPharmacy ERP Team"
                )

            else:
                title = "Subscription Expires Today"

                message = (
                    f"The subscription for {retailer_name} "
                    f"expires today ({expiry_date})."
                )

                email_subject = (
                    "Pharmacy ERP - Subscription Expires Today"
                )

                email_message = (
                    f"Hello,\n\n"
                    f"Your subscription for {retailer_name} "
                    f"expires today, {expiry_date}.\n\n"
                    "Please contact the Platform Support Team "
                    "to renew your subscription.\n\n"
                    "Regards,\nPharmacy ERP Team"
                )

            with transaction.atomic():

                create_subscription_notifications(
                    subscription,
                    Notification.NotificationType.SUBSCRIPTION_EXPIRING_TODAY,
                    title,
                    message,
                )

                send_subscription_email(
                    subscription,
                    Notification.NotificationType.SUBSCRIPTION_EXPIRING_TODAY,
                    email_subject,
                    email_message,
                )

            processed_count += 1

        #-----------------------------------------------------------#
        # Expired Subscription Notification
        #-----------------------------------------------------------#

        if expiry_date < today:

            if is_trial:
                title = "Free Trial Expired"

                message = (
                    f"The free trial for {retailer_name} "
                    f"expired on {expiry_date}. "
                    "Please contact the ERP Team to purchase "
                    "a subscription plan."
                )

                email_subject = "Pharmacy ERP - Free Trial Expired"

                email_message = (
                    f"Hello,\n\n"
                    f"Your free trial for {retailer_name} "
                    f"expired on {expiry_date}.\n\n"
                    "To continue using Pharmacy ERP, please "
                    "contact the ERP Team to purchase "
                    "a subscription plan.\n\n"
                    "Regards,\nPharmacy ERP Team"
                )

            else:
                title = "Subscription Expired"

                message = (
                    f"The subscription for {retailer_name} "
                    f"expired on {expiry_date}. "
                    "Please review the subscription and renewal status."
                )

                email_subject = (
                    "Pharmacy ERP - Subscription Expired"
                )

                email_message = (
                    f"Hello,\n\n"
                    f"Your subscription for {retailer_name} "
                    f"expired on {expiry_date}.\n\n"
                    "Please contact the Platform Support Team "
                    "to renew your subscription.\n\n"
                    "Regards,\nPharmacy ERP Team"
                )

            with transaction.atomic():

                create_subscription_notifications(
                    subscription,
                    Notification.NotificationType.SUBSCRIPTION_EXPIRED,
                    title,
                    message,
                )

                send_subscription_email(
                    subscription,
                    Notification.NotificationType.SUBSCRIPTION_EXPIRED,
                    email_subject,
                    email_message,
                )

            processed_count += 1

    return processed_count