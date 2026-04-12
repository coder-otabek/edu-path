"""
core/admin.py
Admin panelda sayt sozlamalarini boshqarish
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    SiteSettings, NavbarExtraLink,
    FooterSettings, FooterColumn, FooterLink,
    AISettings, DrawerLink,
    VideoLesson, VideoProgress,
)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('🎨 Branding', {
            'fields': ('name', 'short_name', 'tagline', 'logo', 'favicon')
        }),
        ('📄 SEO', {
            'fields': ('meta_description',)
        }),
        ('🔐 Auth Sahifalar', {
            'fields': (
                'login_title', 'login_subtitle',
                'register_title', 'register_subtitle',
                'auth_hero_title', 'auth_hero_sub',
            ),
            'classes': ('collapse',)
        }),
        ('📧 Email / SMTP Sozlamalari', {
            'fields': (
                'official_email', 'smtp_host', 'smtp_port',
                'smtp_email', 'smtp_password', 'smtp_use_tls',
            ),
            'description': 'Forgot password uchun SMTP sozlamalari'
        }),
        ('📞 Aloqa', {
            'fields': ('phone', 'address'),
            'classes': ('collapse',)
        }),
        ('🌐 Ijtimoiy Tarmoqlar', {
            'fields': ('telegram', 'instagram', 'facebook', 'youtube', 'linkedin'),
            'classes': ('collapse',)
        }),
        ('⚙️ Tizim', {
            'fields': ('maintenance_mode', 'allow_register'),
        }),
    )
    readonly_fields = ['logo_preview']

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="60" style="border-radius:8px">', obj.logo.url)
        return "—"
    logo_preview.short_description = "Logo"


@admin.register(NavbarExtraLink)
class NavbarExtraLinkAdmin(admin.ModelAdmin):
    list_display       = ['order', 'name', 'url', 'is_active', 'open_new_tab']
    list_display_links = ['name']   # ← order ni link emas qiladi
    list_editable      = ['order', 'is_active']
    ordering           = ['order']


@admin.register(DrawerLink)
class DrawerLinkAdmin(admin.ModelAdmin):
    list_display       = ['order', 'name', 'url', 'is_active', 'open_new_tab']
    list_display_links = ['name']
    list_editable      = ['order', 'is_active']
    ordering           = ['order']


class FooterLinkInline(admin.TabularInline):
    model  = FooterLink
    extra  = 1
    fields = ['name', 'url', 'order', 'open_new_tab']


class FooterColumnInline(admin.StackedInline):
    model   = FooterColumn
    extra   = 1
    inlines = [FooterLinkInline]


@admin.register(FooterSettings)
class FooterSettingsAdmin(admin.ModelAdmin):
    inlines = [FooterColumnInline]

    def has_add_permission(self, request):
        return not FooterSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AISettings)
class AISettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('🤖 AI Provider', {
            'fields': ('provider', 'api_key', 'model_name', 'is_active')
        }),
        ('⚙️ Parametrlar', {
            'fields': ('max_tokens', 'temperature', 'notes'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['api_key_display']

    def has_add_permission(self, request):
        return not AISettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def api_key_display(self, obj):
        if obj.api_key:
            return f"{'*' * 20}{obj.api_key[-4:]}"
        return "—"
    api_key_display.short_description = "API Key"


@admin.register(VideoLesson)
class VideoLessonAdmin(admin.ModelAdmin):
    list_display       = ['order', 'title', 'is_active', 'created_at']
    list_display_links = ['title']  # ← xatoni tuzatadi
    list_editable      = ['order', 'is_active']
    ordering           = ['order']


@admin.register(VideoProgress)
class VideoProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'video', 'watched', 'position', 'updated_at']
    list_filter  = ['watched']