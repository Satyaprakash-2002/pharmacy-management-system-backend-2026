
from django.contrib.auth.models import AbstractUser
from django.db import models


# Custom User model for the Pharmacy Management System.
# Uses Django's built-in authentication system.
class User(AbstractUser):

    # Defines the roles available in the system.
    class Role(models.TextChoices):
        PLATFORM_OWNER = "PLATFORM_OWNER", "Super User"
        RETAILER_ADMIN = "RETAILER_ADMIN", "Super Admin"
        BRANCH_ADMIN = "BRANCH_ADMIN", "Admin"
        PHARMACIST = "PHARMACIST", "Pharmacist"
        CASHIER = "CASHIER", "Cashier"
        STAFF = "STAFF", "Staff"

    # Stores the role of the user.
    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.STAFF,
    )

    # Retailer to which the user belongs.
    # Super User does not belong to a specific retailer.
    retailer = models.ForeignKey(
        "retailers.Retailer",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users",
    )

    # Branch to which the user belongs.
    # Super User and Super Admin can have no specific branch.
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users",
    )