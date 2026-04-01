from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AdminOperationLog(TimeStampedModel):
    MODULE_CHOICES = [
        ("users", "Users"),
        ("recipes", "Recipes"),
        ("community", "Community"),
        ("reports", "Reports"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="admin_operation_logs",
    )
    module = models.CharField(max_length=32, choices=MODULE_CHOICES)
    action = models.CharField(max_length=64)
    target_type = models.CharField(max_length=64, blank=True, default="")
    target_id = models.BigIntegerField(null=True, blank=True)
    target_label = models.CharField(max_length=255, blank=True, default="")
    summary = models.CharField(max_length=255)
    changes = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "admin_operation_log"
        ordering = ["-created_at", "-id"]
