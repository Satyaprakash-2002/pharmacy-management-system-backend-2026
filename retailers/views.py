# -----------------------------------------------------------#
# Imports
# -----------------------------------------------------------#

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import RetailerCreateSerializer
from accounts.permissions import IsPlatformOwner


# -----------------------------------------------------------#
# Create Retailer
# -----------------------------------------------------------#

class RetailerCreateView(APIView):

    permission_classes = [IsPlatformOwner]

    def post(self, request):

        serializer = RetailerCreateSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():

            result = serializer.save()

            retailer = result["retailer"]
            super_admin = result["super_admin"]
            default_branch = result["default_branch"]
            subscription = result["subscription"]
            plan = subscription.plan

            return Response(
                {
                    "message": (
                        "Retailer, Retailer Admin, default branch, "
                        "and subscription created successfully."
                    ),

                    "retailer": {
                        "id": retailer.id,
                        "name": retailer.name,
                    },

                    "retailer_admin": {
                        "id": super_admin.id,
                        "username": super_admin.username,
                        "email": super_admin.email,
                        "role": super_admin.role,
                    },

                    "default_branch": {
                        "id": default_branch.id,
                        "name": default_branch.name,
                        "address": default_branch.address,
                        "phone": default_branch.phone,
                        "is_active": default_branch.is_active,
                    },

                    "subscription": {
                        "id": subscription.id,
                        "plan_id": plan.id,
                        "plan_name": plan.name,
                        "plan_type": (
                            "Trial" if plan.is_trial else "Paid"
                        ),
                        "price": str(plan.price),
                        "duration_months": plan.duration_months,
                        "trial_duration_days": (
                            plan.trial_duration_days if plan.is_trial else None
                        ),
                        "max_branches": plan.max_branches,
                        "max_users": plan.max_users,
                        "max_medicines": plan.max_medicines,
                        "start_date": subscription.start_date,
                        "end_date": subscription.end_date,
                        "status": subscription.status,
                        "trial_branch_id": subscription.trial_branch_id,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )
