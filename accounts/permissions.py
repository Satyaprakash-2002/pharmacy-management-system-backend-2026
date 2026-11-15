from rest_framework.permissions import BasePermission
from .models import User
from django.utils import timezone
from subscriptions.models import Subscription


class IsPlatformOwner(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.PLATFORM_OWNER
        )


class IsRetailerAdmin(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.RETAILER_ADMIN
        )


class IsBranchAdmin(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.BRANCH_ADMIN
        )


class IsRetailerOrBranchAdmin(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                User.Role.RETAILER_ADMIN,
                User.Role.BRANCH_ADMIN,
            ]
        )

#-----------------------------------------------------------#
# Expired Subscription Read-Only Permission
#-----------------------------------------------------------#

class IsSubscriptionActiveOrReadOnly(BasePermission):

    def has_permission(self, request, view):

        user = request.user

        if not user or not user.is_authenticated:
            return False

        # Platform Owner has unrestricted access.
        if user.role == User.Role.PLATFORM_OWNER:
            return True

        # Allow read-only requests.
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        # Check whether the retailer has an active subscription.
        if not user.retailer:
            return False

        today = timezone.localdate()

        return Subscription.objects.filter(
            retailer=user.retailer,
            status=Subscription.Status.ACTIVE,
            start_date__lte=today,
            end_date__gte=today,
            retailer__is_active=True,
            plan__is_active=True,
        ).exists()