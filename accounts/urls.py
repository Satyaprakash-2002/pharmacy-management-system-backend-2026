# from django.urls import path

# from .views import (
#     LoginView,
#     PasswordSetupView,
#     # CreateSuperAdminView,
#     CreateAdminView,
#     CreateBranchUserView,
#     RetailerUserListView,
#     BranchUserListView,
#     UserUpdateView,
# )


# urlpatterns = [

#     path(
#         "login/",
#         LoginView.as_view(),
#         name="login",
#     ),

#     #-----------------------------------------------------------#
#      # Password Setup
#     #-----------------------------------------------------------#

#     path(
#         "set-password/",
#         PasswordSetupView.as_view(),
#         name="set-password",
#     ),

#     # path(
#     #     "create-super-admin/",
#     #     CreateSuperAdminView.as_view(),
#     #     name="create-super-admin",
#     # ),

#     path(
#         "create-admin/",
#         CreateAdminView.as_view(),
#         name="create-admin",
#     ),

#     path(
#         "create-branch-user/",
#         CreateBranchUserView.as_view(),
#         name="create-branch-user",
#     ),

#     path(
#         "retailer-users/",
#         RetailerUserListView.as_view(),
#         name="retailer-user-list",
#     ),

#     path(
#        "branch-users/",
#        BranchUserListView.as_view(),
#        name="branch-user-list",
#     ),

#     path(
#        "users/<int:user_id>/",
#        UserUpdateView.as_view(),
#        name="user-update",
#     ),
# ]



from django.urls import path

from .views import (
    LoginView,
    PasswordSetupView,
    # CreateSuperAdminView,
    CreateAdminView,
    CreateBranchUserView,
    RetailerUserListView,
    BranchUserListView,
    UserUpdateView,
)


urlpatterns = [

    #-----------------------------------------------------------#
    # Login
    #-----------------------------------------------------------#

    path(
        "login/",
        LoginView.as_view(),
        name="login",
    ),

    #-----------------------------------------------------------#
    # Password Setup
    #-----------------------------------------------------------#

    path(
        "set-password/",
        PasswordSetupView.as_view(),
        name="set-password",
    ),

    # path(
    #     "create-super-admin/",
    #     CreateSuperAdminView.as_view(),
    #     name="create-super-admin",
    # ),

    #-----------------------------------------------------------#
    # Create Branch Admin
    #-----------------------------------------------------------#

    path(
        "create-admin/",
        CreateAdminView.as_view(),
        name="create-admin",
    ),

    #-----------------------------------------------------------#
    # Create Branch User
    #-----------------------------------------------------------#

    path(
        "create-branch-user/",
        CreateBranchUserView.as_view(),
        name="create-branch-user",
    ),

    #-----------------------------------------------------------#
    # Retailer User List
    #-----------------------------------------------------------#

    path(
        "retailer-users/",
        RetailerUserListView.as_view(),
        name="retailer-user-list",
    ),

    #-----------------------------------------------------------#
    # Branch User List
    #-----------------------------------------------------------#

    path(
        "branch-users/",
        BranchUserListView.as_view(),
        name="branch-user-list",
    ),

    #-----------------------------------------------------------#
    # User Update
    #-----------------------------------------------------------#

    path(
        "users/<int:user_id>/",
        UserUpdateView.as_view(),
        name="user-update",
    ),
]
