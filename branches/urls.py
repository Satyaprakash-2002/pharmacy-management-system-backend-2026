from django.urls import path

from .views import (
    CreateBranchView,
    BranchListView,
    BranchUpdateView,
    BranchStatusView,
)

urlpatterns = [
    path(
        "create/",
        CreateBranchView.as_view(),
        name="create-branch",
    ),

    path(
        "",
        BranchListView.as_view(),
        name="branch-list",
    ),

    path(
        "<int:branch_id>/",
        BranchUpdateView.as_view(),
        name="update-branch",
    ),

    path(
        "<int:branch_id>/status/",
        BranchStatusView.as_view(),
        name="branch-status",
    ),
]