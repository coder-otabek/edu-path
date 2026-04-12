from django.contrib import admin
from .models import RoadMap, ChatSession, ChatMessage

@admin.register(RoadMap)
class RoadMapAdmin(admin.ModelAdmin):
    list_display = ['user', 'ai_provider', 'generated_at']
    readonly_fields = ['content', 'generated_at']

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ['role', 'content', 'created_at']

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'updated_at']
    inlines = [ChatMessageInline]
