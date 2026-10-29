
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


#-----------------------------------------------------------#
# Custom User Model
#-----------------------------------------------------------#

# Extends Django's built-in AbstractUser model.
# Stores user authentication details, roles, and relationships
# with retailers and branches.
class User(AbstractUser):

    # Defines the roles available in the Pharmacy Management System.
    class Role(models.TextChoices):
        PLATFORM_OWNER = "PLATFORM_OWNER", "Super User"
        RETAILER_ADMIN = "RETAILER_ADMIN", "Super Admin"
        BRANCH_ADMIN = "BRANCH_ADMIN", "Admin"
        PHARMACIST = "PHARMACIST", "Pharmacist"
        CASHIER = "CASHIER", "Cashier"
        STAFF = "STAFF", "Staff"

    # Stores the role assigned to the user.
    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.STAFF,
    )

    # Retailer to which the user belongs.
    # Platform Owner does not belong to a specific retailer.
    retailer = models.ForeignKey(
        "retailers.Retailer",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users",
    )

    # Branch to which the user belongs.
    # Platform Owner and Retailer Admin may have no specific branch.
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users",
    )

    # Automatically assigns Platform Owner role to superusers.
    # Superusers are not associated with a retailer or branch.
    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.PLATFORM_OWNER
            self.retailer = None
            self.branch = None

        super().save(*args, **kwargs)


#-----------------------------------------------------------#
# Password Setup Token
#-----------------------------------------------------------#

# Stores password setup token information for newly created users.
# Only the hashed token is stored in the database.
# The raw token is shared with the user through a secure email link.
class PasswordSetupToken(models.Model):

    # User who is allowed to set their password using this token.
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_setup_tokens",
    )

    # Stores the SHA-256 hash of the password setup token.
    # The hash must be unique for every token.
    token_hash = models.CharField(
        max_length=64,
        unique=True,
    )

    # Date and time after which the token can no longer be used.
    # The token-generation logic will set this to 24 hours
    # after the token is created.
    expires_at = models.DateTimeField()

    # Records when the token was used successfully.
    # None means the token has not yet been used.
    used_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Records when the token entry was created.
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    # Displays the newest password setup tokens first.
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Password Setup Token"
        verbose_name_plural = "Password Setup Tokens"

    # Checks whether the token is unused, unexpired,
    # and associated with an active user.
    def is_valid(self):
        return (
            self.used_at is None
            and self.expires_at > timezone.now()
            and self.user.is_active
        )

    # Returns a readable description of the token record.
    def __str__(self):
        return f"Password setup token for {self.user.username}"
