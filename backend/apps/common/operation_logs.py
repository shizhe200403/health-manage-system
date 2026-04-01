from datetime import date, datetime
from decimal import Decimal

from rest_framework import permissions

from .models import AdminOperationLog


def is_admin_operator(user):
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or user.is_staff or getattr(user, "role", "") in {"admin", "auditor"})
    )


class IsAdminOperatorPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_admin_operator(request.user)


def serialize_log_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, list):
        return [serialize_log_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): serialize_log_value(item) for key, item in value.items()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def snapshot_model_fields(instance, fields):
    snapshot = {}
    for field in fields:
        snapshot[field] = serialize_log_value(getattr(instance, field, None))
    return snapshot


def build_change_entries(before, after, field_labels=None, section=None):
    labels = field_labels or {}
    changes = []
    ordered_fields = list(dict.fromkeys([*before.keys(), *after.keys()]))
    for field in ordered_fields:
        before_value = before.get(field)
        after_value = after.get(field)
        if before_value == after_value:
            continue
        changes.append(
            {
                "section": section or "",
                "field": field,
                "label": labels.get(field, field),
                "before": before_value,
                "after": after_value,
            }
        )
    return changes


def create_admin_operation_log(
    *,
    actor,
    module,
    action,
    target_type="",
    target_id=None,
    target_label="",
    summary,
    changes=None,
    metadata=None,
):
    if not is_admin_operator(actor):
        return None
    return AdminOperationLog.objects.create(
        actor=actor,
        module=module,
        action=action,
        target_type=target_type,
        target_id=target_id,
        target_label=target_label,
        summary=summary,
        changes=changes or [],
        metadata=metadata or {},
    )
