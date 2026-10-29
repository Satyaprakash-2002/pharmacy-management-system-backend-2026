
from django.urls import path

from .views import (
    PlanListCreateView,
    PlanDetailView,
    PlanStatusView,
    SubscriptionListCreateView,
    SubscriptionDetailView,
    ChangeSubscriptionPlanView,
    TrialBranchSelectionView,
)


urlpatterns = [
    # -----------------------------------------------------------#
    # Plan Management
    # -----------------------------------------------------------#
    path(
        "plans/",
        PlanListCreateView.as_view(),
        name="plan-list-create",
    ),
    path(
        "plans/<int:pk>/",
        PlanDetailView.as_view(),
        name="plan-detail",
    ),
    path(
        "plans/<int:pk>/status/",
        PlanStatusView.as_view(),
        name="plan-status",
    ),

    # -----------------------------------------------------------#
    # Subscription Management
    # -----------------------------------------------------------#
    path(
        "subscriptions/",
        SubscriptionListCreateView.as_view(),
        name="subscription-list-create",
    ),
    path(
        "subscriptions/<int:pk>/",
        SubscriptionDetailView.as_view(),
        name="subscription-detail",
    ),

    path(
        "change-plan/",
        ChangeSubscriptionPlanView.as_view(),
        name="subscription-change-plan",
    ),

    # -----------------------------------------------------------#
    # Free Trial Branch Selection
    # -----------------------------------------------------------#
    path(
        "trial/select-branch/",
        TrialBranchSelectionView.as_view(),
        name="select-trial-branch",
    ),
]
