
# -----------------------------------------------------------#
# Imports
# -----------------------------------------------------------#

from django.db import models
from django.conf import settings


# -----------------------------------------------------------#
# Notification Model
# -----------------------------------------------------------#

class Notification(models.Model):

    # -----------------------------------------------------------#
    # Notification Types
    # -----------------------------------------------------------#

    class NotificationType(models.TextChoices):
        SUBSCRIPTION_EXPIRING = (
            "SUBSCRIPTION_EXPIRING",
            "Subscription Expiring Soon",
        )

        SUBSCRIPTION_EXPIRING_TODAY = (
            "SUBSCRIPTION_EXPIRING_TODAY",
            "Subscription Expires Today",
        )

        SUBSCRIPTION_EXPIRED = (
            "SUBSCRIPTION_EXPIRED",
            "Subscription Expired",
        )

    # -----------------------------------------------------------#
    # Notification Recipient
    # -----------------------------------------------------------#

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    # -----------------------------------------------------------#
    # Related Subscription
    # -----------------------------------------------------------#

    subscription = models.ForeignKey(
        "subscriptions.Subscription",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )

    # -----------------------------------------------------------#
    # Notification Details
    # -----------------------------------------------------------#

    title = models.CharField(max_length=200)

    message = models.TextField()

    notification_type = models.CharField(
        max_length=40,
        choices=NotificationType.choices,
    )

    # -----------------------------------------------------------#
    # Duplicate Prevention
    # -----------------------------------------------------------#

    event_key = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True,
    )

    # -----------------------------------------------------------#
    # Email Tracking
    # -----------------------------------------------------------#

    email_sent = models.BooleanField(default=False)

    # -----------------------------------------------------------#
    # Read Status
    # -----------------------------------------------------------#

    is_read = models.BooleanField(default=False)

    # -----------------------------------------------------------#
    # Timestamp
    # -----------------------------------------------------------#

    created_at = models.DateTimeField(auto_now_add=True)

    # -----------------------------------------------------------#
    # Model Ordering
    # -----------------------------------------------------------#

    class Meta:
        ordering = ["-created_at"]

    # -----------------------------------------------------------#
    # String Representation
    # -----------------------------------------------------------#

    def __str__(self):
        return f"{self.title} - {self.recipient.username}"


# -----------------------------------------------------------#
# Subscription Email Log Model
# -----------------------------------------------------------#

class SubscriptionEmailLog(models.Model):

    #-----------------------------------------------------------#
    # Related Subscription
    #-----------------------------------------------------------#

    subscription = models.ForeignKey(
        "subscriptions.Subscription",
        on_delete=models.CASCADE,
        related_name="email_logs",
    )

    #-----------------------------------------------------------#
    # Email Notification Type
    #-----------------------------------------------------------#

    notification_type = models.CharField(
        max_length=40,
        choices=Notification.NotificationType.choices,
    )

    #-----------------------------------------------------------#
    # Email Recipient
    #-----------------------------------------------------------#

    recipient_email = models.EmailField()

    #-----------------------------------------------------------#
    # Duplicate Email Prevention
    #-----------------------------------------------------------#

    event_key = models.CharField(
        max_length=150,
        unique=True,
    )

    #-----------------------------------------------------------#
    # Email Status
    #-----------------------------------------------------------#

    email_sent = models.BooleanField(default=False)

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    #-----------------------------------------------------------#
    # Model Ordering
    #-----------------------------------------------------------#

    class Meta:
        ordering = ["-created_at"]

    #-----------------------------------------------------------#
    # String Representation
    #-----------------------------------------------------------#

    def __str__(self):
        return f"{self.notification_type} - {self.recipient_email}"
