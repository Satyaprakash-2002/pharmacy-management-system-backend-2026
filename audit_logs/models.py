
from django.conf import settings
from django.db import models


# -----------------------------------------------------------#
# Common Audit Log Fields
# -----------------------------------------------------------#

class BaseAuditLog(models.Model):

    class Action(models.TextChoices):
        CREATE = "CREATE", "Created"
        UPDATE = "UPDATE", "Updated"
        DELETE = "DELETE", "Deleted"
        ACTIVATE = "ACTIVATE", "Activated"
        DEACTIVATE = "DEACTIVATE", "Deactivated"
        SEND = "SEND", "Sent"
        READ = "READ", "Read"
        FAILED = "FAILED", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    retailer = models.ForeignKey(
        "retailers.Retailer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    action = models.CharField(
        max_length=20,
        choices=Action.choices,
    )

    object_id = models.CharField(
        max_length=64,
    )

    object_name = models.CharField(
        max_length=255,
        blank=True,
    )

    old_values = models.JSONField(
        default=dict,
        blank=True,
    )

    new_values = models.JSONField(
        default=dict,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]


# -----------------------------------------------------------#
# Accounts Audit Log
# -----------------------------------------------------------#

class AccountAuditLog(BaseAuditLog):

    class Meta(BaseAuditLog.Meta):
        verbose_name = "Account Audit Log"
        verbose_name_plural = "Account Audit Logs"

    def __str__(self):
        return f"{self.action} - Account {self.object_id}"


# -----------------------------------------------------------#
# Retailers Audit Log
# -----------------------------------------------------------#

class RetailerAuditLog(BaseAuditLog):

    class Meta(BaseAuditLog.Meta):
        verbose_name = "Retailer Audit Log"
        verbose_name_plural = "Retailer Audit Logs"

    def __str__(self):
        return f"{self.action} - Retailer {self.object_id}"


# -----------------------------------------------------------#
# Branches Audit Log
# -----------------------------------------------------------#

class BranchAuditLog(BaseAuditLog):

    class Meta(BaseAuditLog.Meta):
        verbose_name = "Branch Audit Log"
        verbose_name_plural = "Branch Audit Logs"

    def __str__(self):
        return f"{self.action} - Branch {self.object_id}"


# -----------------------------------------------------------#
# Subscriptions Audit Log
# -----------------------------------------------------------#

class SubscriptionAuditLog(BaseAuditLog):

    class Meta(BaseAuditLog.Meta):
        verbose_name = "Subscription Audit Log"
        verbose_name_plural = "Subscription Audit Logs"

    def __str__(self):
        return f"{self.action} - Subscription {self.object_id}"


# -----------------------------------------------------------#
# Notifications Audit Log
# -----------------------------------------------------------#

class NotificationAuditLog(BaseAuditLog):

    class Meta(BaseAuditLog.Meta):
        verbose_name = "Notification Audit Log"
        verbose_name_plural = "Notification Audit Logs"

    def __str__(self):
        return f"{self.action} - Notification {self.object_id}"
