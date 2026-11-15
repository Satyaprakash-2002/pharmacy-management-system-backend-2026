
# Django REST Framework Imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Django Imports
from django.shortcuts import get_object_or_404

# Local App Imports
from accounts.permissions import IsPlatformOwner
from .models import Notification


#-----------------------------------------------------------#
# Get All Notifications API
#-----------------------------------------------------------#
class NotificationListAPIView(APIView):

    permission_classes = [IsPlatformOwner]

    def get(self, request):

        notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by("-created_at")

        data = []

        for notification in notifications:
            data.append({
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "notification_type": notification.notification_type,
                "is_read": notification.is_read,
                "created_at": notification.created_at,
            })

        return Response({
            "success": True,
            "count": len(data),
            "notifications": data,
        }, status=status.HTTP_200_OK)


#-----------------------------------------------------------#
# Get Unread Notification Count API
#-----------------------------------------------------------#
class UnreadNotificationCountAPIView(APIView):

    permission_classes = [IsPlatformOwner]

    def get(self, request):

        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        return Response({
            "success": True,
            "unread_count": unread_count,
        }, status=status.HTTP_200_OK)


#-----------------------------------------------------------#
# Mark Single Notification as Read API
#-----------------------------------------------------------#
class MarkNotificationAsReadAPIView(APIView):

    permission_classes = [IsPlatformOwner]

    def patch(self, request, notification_id):

        notification = get_object_or_404(
            Notification,
            id=notification_id,
            recipient=request.user
        )

        notification.is_read = True
        notification.save(update_fields=["is_read"])

        return Response({
            "success": True,
            "message": "Notification marked as read.",
            "notification_id": notification.id,
            "is_read": notification.is_read,
        }, status=status.HTTP_200_OK)


#-----------------------------------------------------------#
# Mark All Notifications as Read API
#-----------------------------------------------------------#
class MarkAllNotificationsAsReadAPIView(APIView):

    permission_classes = [IsPlatformOwner]

    def patch(self, request):

        updated_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)

        return Response({
            "success": True,
            "message": "All notifications marked as read.",
            "updated_count": updated_count,
        }, status=status.HTTP_200_OK)
