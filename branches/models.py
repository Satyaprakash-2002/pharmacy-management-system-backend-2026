from django.db import models
from retailers.models import Retailer


class Branch(models.Model):
    # Retailer that owns this branch.
    retailer = models.ForeignKey(
        Retailer,
        on_delete=models.CASCADE,
        related_name="branches",
    )

    # Name of the branch.
    name = models.CharField(max_length=150)

    # Physical address of the branch.
    address = models.TextField()

    # Contact number of the branch.
    phone = models.CharField(max_length=15)

    # Indicates whether the branch is currently active.
    is_active = models.BooleanField(default=True)

    # Automatically stores when the branch was created.
    created_at = models.DateTimeField(auto_now_add=True)

    # Automatically updates whenever the branch is modified.
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.retailer.name} - {self.name}"