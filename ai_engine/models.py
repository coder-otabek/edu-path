"""ai_engine/models.py"""
from django.db import models
from accounts.models import CustomUser


class RoadMap(models.Model):
    user       = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='roadmap')
    content    = models.JSONField("Road map content", default=dict)
    generated_at = models.DateTimeField(auto_now=True)
    ai_provider  = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "Road Map"

    def __str__(self):
        return f"{self.user.email} — Road Map"


class ChatSession(models.Model):
    user       = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='chat_sessions')
    title      = models.CharField(max_length=255, default="Yangi suhbat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Chat Sessiya"
        verbose_name_plural = "Chat Sessiyalar"
        ordering            = ['-updated_at']

    def __str__(self):
        return f"{self.user.email} — {self.title}"


class ChatMessage(models.Model):
    ROLE_CHOICES = [('user', 'Foydalanuvchi'), ('assistant', 'AI')]
    session    = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role       = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Chat Xabar"
        verbose_name_plural = "Chat Xabarlar"
        ordering            = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"
