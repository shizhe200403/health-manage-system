from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class Conversation(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=100, default="新对话")

    class Meta:
        db_table = "assistant_conversation"
        ordering = ["-updated_at"]


class Message(TimeStampedModel):
    ROLE_CHOICES = [("user", "User"), ("assistant", "Assistant"), ("system", "System")]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    content = models.TextField()

    class Meta:
        db_table = "assistant_message"
        ordering = ["created_at"]
