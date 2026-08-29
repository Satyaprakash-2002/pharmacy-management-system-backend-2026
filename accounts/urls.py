from django.urls import path

from .views import (
    CreateSuperAdminView,
    CreateAdminView,
    CreateBranchUserView,
)


urlpatterns = [
    path(
        "create-super-admin/",
        CreateSuperAdminView.as_view(),
        name="create-super-admin",
    ),

    path(
        "create-admin/",
        CreateAdminView.as_view(),
        name="create-admin",
    ),

    path(
        "create-branch-user/",
        CreateBranchUserView.as_view(),
        name="create-branch-user",
    ),
]