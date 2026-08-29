from rest_framework.permissions import BasePermission
from .models import User


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