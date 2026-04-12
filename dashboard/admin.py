from django.contrib import admin
from .models import Essay

@admin.register(Essay)
class EssayAdmin(admin.ModelAdmin):
    list_display  = ['user', 'title', 'essay_type', 'status', 'ai_score', 'word_count', 'created_at']
    list_filter   = ['status', 'essay_type']
    search_fields = ['user__email', 'title']
    readonly_fields = ['ai_score', 'ai_feedback', 'ai_strengths', 'ai_weaknesses', 'ai_suggestions', 'ai_reviewed_at', 'word_count']