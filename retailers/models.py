from django.db import models


class Retailer(models.Model):
    # Name of the pharmacy/retail business.
    name = models.CharField(max_length=150)

    # Indicates whether the retailer is currently active.
    is_active = models.BooleanField(default=True)

    # Automatically stores when the retailer was created.
    created_at = models.DateTimeField(auto_now_add=True)

    # Automatically updates whenever the retailer is modified.
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name