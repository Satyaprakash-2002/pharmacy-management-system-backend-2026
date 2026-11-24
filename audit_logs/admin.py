from django.contrib import admin

from .models import (
    AccountAuditLog,
    RetailerAuditLog,
    BranchAuditLog,
    SubscriptionAuditLog,
    NotificationAuditLog,
)


admin.site.register(AccountAuditLog)
admin.site.register(RetailerAuditLog)
admin.site.register(BranchAuditLog)
admin.site.register(SubscriptionAuditLog)
admin.site.register(NotificationAuditLog)