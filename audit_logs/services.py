from .models import (
    AccountAuditLog,
    RetailerAuditLog,
    BranchAuditLog,
    SubscriptionAuditLog,
    NotificationAuditLog,
)


# -----------------------------------------------------------#
# Audit Log Model Mapping
# -----------------------------------------------------------#

AUDIT_LOG_MODELS = {
    "accounts": AccountAuditLog,
    "retailers": RetailerAuditLog,
    "branches": BranchAuditLog,
    "subscriptions": SubscriptionAuditLog,
    "notifications": NotificationAuditLog,
}


# -----------------------------------------------------------#
# Create Audit Log
# -----------------------------------------------------------#

def create_audit_log(
    module,
    user,
    action,
    object_id,
    object_name="",
    retailer=None,
    branch=None,
    old_values=None,
    new_values=None,
    description="",
):
    AuditLog = AUDIT_LOG_MODELS[module]

    return AuditLog.objects.create(
        user=user,
        retailer=retailer,
        branch=branch,
        action=action,
        object_id=str(object_id),
        object_name=object_name,
        old_values=old_values or {},
        new_values=new_values or {},
        description=description,
    )