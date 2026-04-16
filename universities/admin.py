"""universities/admin.py"""
from django.contrib import admin
from django.utils.html import format_html
from django.core.exceptions import ValidationError
# nested_admin'dan kerakli klasslarni chaqiramiz
from nested_admin import NestedTabularInline, NestedStackedInline, NestedModelAdmin

from .models import (
    University, Specialty, Grant, GrantVideo,
    UniversityContent, EssaySample,
    StandaloneGrant, StandaloneGrantVideo,
    GrantTest, GrantQuestion, GrantChoice, GrantTestResult,
)

# ─── Specialty ───────────────────────────────────────────────
@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display  = ['name']

# ─── ODDIY INLINE'LAR ────────────────────────────────────────

class GrantVideoInline(admin.TabularInline):
    model    = GrantVideo
    extra    = 1
    fields   = ['title', 'order', 'youtube_url', 'video_file', 'duration', 'is_published']
    ordering = ['order']

class GrantInline(admin.StackedInline):
    model  = Grant
    extra  = 0
    fields = ['name', 'grant_type', 'degree', 'amount', 'deadline', 'deadline_text',
              'min_ielts', 'min_gpa', 'requirements', 'description', 'is_active']
    show_change_link = True

class UniversityContentInline(admin.TabularInline):
    model           = UniversityContent
    extra           = 0
    fields          = ['title', 'content_type', 'file', 'text_content', 'ai_processed']
    readonly_fields = ['ai_processed']

class StandaloneGrantVideoInline(admin.TabularInline):
    model    = StandaloneGrantVideo
    extra    = 1
    fields   = ['title', 'order', 'youtube_url', 'video_file', 'duration', 'is_published']
    ordering = ['order']

# ─── NESTED INLINE'LAR (SAVOL VA VARIANTLAR) ──────────────────

class GrantChoiceInline(NestedTabularInline):
    """Eng ichki qatlam: Javob variantlari"""
    model      = GrantChoice
    extra      = 4
    min_num    = 3
    max_num    = 4
    fields     = ['text', 'is_correct', 'order']
    ordering   = ['order']

class GrantQuestionInline(NestedStackedInline):
    """O'rta qatlam: Savollar"""
    model   = GrantQuestion
    extra   = 1
    inlines = [GrantChoiceInline] # Savol ichida variantlar chiqadi
    fields  = ['text', 'order', 'explanation']
    # 'collapse' klassini olib tashladik, Jazzmin bilan yaxshiroq chiqishi uchun
    classes = ['extrapretty']

# ─── GRANT TEST (ASOSIY ADMIN) ──────────────────────────────

@admin.register(GrantTest)
class GrantTestAdmin(NestedModelAdmin): # NestedModelAdmin muhim!
    list_display  = ['title', 'video_display', 'is_active']
    inlines       = [GrantQuestionInline] # Test ichida savollar va variantlar
    save_on_top   = True

    # MUHIM: Jazzmin tablarini test qilish uchun fieldsets'ni soddalashtiramiz
    fieldsets = (
        ("Test Sozlamalari", {
            'fields': ('video', 'is_active', 'title', 'description', 'time_limit', 'pass_percent'),
        }),
    )

    def video_display(self, obj):
        try:
            return f"{obj.video.grant.name} | {obj.video.title}"
        except:
            return "—"
    video_display.short_description = "Video dars"

# ─── QOLGAN ADMINLAR ────────────────────────────────────────

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'city', 'is_published']
    inlines      = [GrantInline, UniversityContentInline]
    # ... qolgan kodlar o'zgarishsiz qoladi

@admin.register(StandaloneGrant)
class StandaloneGrantAdmin(admin.ModelAdmin):
    list_display        = ['order', 'name', 'grant_type', 'country', 'is_active']
    list_editable       = ['order', 'is_active']
    list_display_links  = ['name']
    list_filter         = ['grant_type', 'country', 'is_active']
    search_fields       = ['name', 'description']
    ordering            = ['order', 'name']
    inlines             = [StandaloneGrantVideoInline]
    save_on_top         = True
    fieldsets = (
        ("Asosiy ma'lumotlar", {
            'fields': ('order', 'name', 'slug', 'grant_type', 'country', 'degree', 'is_active'),
        }),
        ("Rasm", {
            'fields': ('cover_image', 'logo'),
            'classes': ('collapse',),
        }),
        ("Tafsilotlar", {
            'fields': ('description', 'founded_year', 'directions', 'requirements',
                       'winners_count', 'amount', 'deadline', 'deadline_text'),
        }),
        ("Talablar", {
            'fields': ('min_ielts', 'min_gpa'),
            'classes': ('collapse',),
        }),
        ("Havolalar", {
            'fields': ('apply_url', 'official_site', 'universities'),
            'classes': ('collapse',),
        }),
    )

@admin.register(GrantTestResult)
class GrantTestResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'test', 'score', 'created_at']