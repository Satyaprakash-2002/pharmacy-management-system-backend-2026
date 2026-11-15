from django.urls import path

from .views import (
    NotificationListAPIView,
    UnreadNotificationCountAPIView,
    MarkNotificationAsReadAPIView,
    MarkAllNotificationsAsReadAPIView,
)


#-----------------------------------------------------------#
# Notification API URL Patterns
#-----------------------------------------------------------#
urlpatterns = [

    # Get All Notifications
    path(
        "",
        NotificationListAPIView.as_view(),
        name="notification-list"
    ),

    # Get Unread Notification Count
    path(
        "unread-count/",
        UnreadNotificationCountAPIView.as_view(),
        name="unread-notification-count"
    ),

    # Mark Single Notification as Read
    path(
        "<int:notification_id>/read/",
        MarkNotificationAsReadAPIView.as_view(),
        name="mark-notification-read"
    ),

    # Mark All Notifications as Read
    path(
        "mark-all-read/",
        MarkAllNotificationsAsReadAPIView.as_view(),
        name="mark-all-notifications-read"
    ),

]