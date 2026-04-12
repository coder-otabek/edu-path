"""universities/admin.py"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    University, Specialty, Grant, GrantVideo,
    UniversityContent, EssaySample,
    StandaloneGrant, StandaloneGrantVideo,
)


# ─── Specialty ───────────────────────────────────────────────
@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display  = ['name']


# ─── Inlines ─────────────────────────────────────────────────
class GrantVideoInline(admin.TabularInline):
    model   = GrantVideo
    extra   = 1
    fields  = ['title', 'order', 'youtube_url', 'video_file', 'duration', 'is_published']
    ordering = ['order']


class GrantInline(admin.StackedInline):
    model  = Grant
    extra  = 0
    fields = [
        'name', 'grant_type', 'degree', 'amount',
        'deadline', 'deadline_text', 'min_ielts', 'min_gpa',
        'requirements', 'description', 'is_active'
    ]
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


# ─── University ─────────────────────────────────────────────
@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display        = ['name', 'country', 'city', 'grant_type_badge', 'has_grant', 'grant_count', 'is_published']
    list_filter         = ['country', 'grant_type', 'has_grant', 'is_published']
    search_fields       = ['name', 'city']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal   = ['specialties']
    inlines             = [GrantInline, UniversityContentInline]
    readonly_fields     = ['ai_summary', 'created_at', 'updated_at', 'logo_preview']

    fieldsets = (
        ("Asosiy", {
            'fields': ('name', 'slug', 'country', 'city', 'grant_type', 'website',
                       'logo', 'logo_preview', 'cover_image', 'is_published')
        }),
        ("Tavsif", {'fields': ('description', 'ai_summary', 'specialties')}),
        ("Qabul talablari", {'fields': ('min_ielts_score', 'min_sat_score', 'min_gpa')}),
        ("To'lov", {'fields': ('tuition_fee_min', 'tuition_fee_max', 'has_grant')}),
        ("Sanalar", {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def grant_count(self, obj):
        return obj.grants.filter(is_active=True).count()
    grant_count.short_description = "Grant soni"

    def grant_type_badge(self, obj):
        colors = {'foreign': '#2196F3', 'local': '#4CAF50', 'both': '#7c3aed'}
        color  = colors.get(obj.grant_type, '#999')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color, obj.get_grant_type_display()
        )
    grant_type_badge.short_description = "Turi"

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="height:60px;border-radius:8px"/>', obj.logo.url)
        return "—"
    logo_preview.short_description = "Logotip"


# ─── Grant (Universitet) ─────────────────────────────────────
@admin.register(Grant)
class GrantAdmin(admin.ModelAdmin):
    list_display        = ['name', 'university', 'grant_type_badge', 'degree', 'amount', 'video_count', 'is_active']
    list_filter         = ['grant_type', 'degree', 'is_active', 'university__country']
    search_fields       = ['name', 'university__name']
    autocomplete_fields = ['university']
    inlines             = [GrantVideoInline]

    fieldsets = (
        ("Asosiy", {'fields': ('university', 'name', 'slug', 'grant_type', 'degree', 'is_active')}),
        ("Tafsilot", {'fields': ('description', 'amount', 'deadline', 'deadline_text')}),
        ("Talablar", {'fields': ('min_ielts', 'min_gpa', 'requirements')}),
    )

    def grant_type_badge(self, obj):
        colors = {'foreign': '#2196F3', 'local': '#4CAF50', 'both': '#7c3aed'}
        color  = colors.get(obj.grant_type, '#999')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color, obj.get_grant_type_display()
        )
    grant_type_badge.short_description = "Turi"

    def video_count(self, obj):
        cnt = obj.videos.filter(is_published=True).count()
        return format_html('<span style="color:#2196F3">▶ {} video</span>', cnt) if cnt else "—"
    video_count.short_description = "Videolar"


# ─── StandaloneGrant ─────────────────────────────────────────
@admin.register(StandaloneGrant)
class StandaloneGrantAdmin(admin.ModelAdmin):
    list_display        = [
        'name', 'grant_type_badge', 'country', 'degree',
        'founded_year', 'amount', 'video_count', 'uni_count', 'is_active'
    ]
    list_filter         = ['grant_type', 'country', 'degree', 'is_active']
    search_fields       = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal   = ['universities']
    inlines             = [StandaloneGrantVideoInline]
    readonly_fields     = ['cover_preview', 'logo_preview']

    fieldsets = (
        ("Asosiy", {
            'fields': (
                'name', 'slug', 'grant_type', 'country', 'degree',
                'logo', 'logo_preview', 'cover_image', 'cover_preview',
                'is_active'
            )
        }),
        ("Ma'lumotlar", {
            'fields': ('description', 'founded_year', 'directions', 'requirements', 'winners_count')
        }),
        ("Mukofot va muddat", {
            'fields': ('amount', 'deadline', 'deadline_text', 'min_ielts', 'min_gpa')
        }),
        ("Havolalar", {
            'fields': ('apply_url', 'official_site')
        }),
        ("Universitetlar (ixtiyoriy)", {
            'fields': ('universities',),
            'description': "Bo'sh qoldirilsa — umumiy grantlar ro'yxatida ko'rinadi. "
                           "Universitet tanlansa — o'sha universitetning grantlari ichida ham ko'rinadi."
        }),
    )

    def grant_type_badge(self, obj):
        colors = {'foreign': '#2196F3', 'local': '#4CAF50', 'both': '#7c3aed'}
        color  = colors.get(obj.grant_type, '#999')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color, obj.get_grant_type_display()
        )
    grant_type_badge.short_description = "Turi"

    def video_count(self, obj):
        cnt = obj.videos.filter(is_published=True).count()
        return format_html('<span style="color:#2196F3">▶ {} video</span>', cnt) if cnt else "—"
    video_count.short_description = "Videolar"

    def uni_count(self, obj):
        cnt = obj.universities.count()
        return f"🎓 {cnt} ta" if cnt else "Umumiy"
    uni_count.short_description = "Universitetlar"

    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" style="height:80px;border-radius:8px"/>', obj.cover_image.url)
        return "—"
    cover_preview.short_description = "Muqova"

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="height:50px;border-radius:6px"/>', obj.logo.url)
        return "—"
    logo_preview.short_description = "Logotip"


# ─── EssaySample ─────────────────────────────────────────────
@admin.register(EssaySample)
class EssaySampleAdmin(admin.ModelAdmin):
    list_display        = ['title', 'essay_type', 'score_stars', 'language', 'word_count', 'university', 'is_active']
    list_filter         = ['essay_type', 'score', 'language', 'is_active']
    search_fields       = ['title', 'content']
    autocomplete_fields = ['university']
    readonly_fields     = ['word_count']

    fieldsets = (
        ("Asosiy", {'fields': ('title', 'essay_type', 'language', 'university', 'score', 'is_active')}),
        ("Esse matni", {'fields': ('content', 'word_count')}),
        ("AI uchun izoh", {'fields': ('structure_notes',)}),
    )

    def score_stars(self, obj):
        return "⭐" * obj.score
    score_stars.short_description = "Sifat"


# ─── UniversityContent ───────────────────────────────────────
@admin.register(UniversityContent)
class UniversityContentAdmin(admin.ModelAdmin):
    list_display        = ['title', 'university', 'content_type', 'ai_processed']
    list_filter         = ['content_type', 'ai_processed']
    search_fields       = ['title', 'university__name']
    autocomplete_fields = ['university']
    readonly_fields     = ['ai_extracted', 'ai_summary', 'ai_processed']

    actions = ['process_with_ai']

    def process_with_ai(self, request, queryset):
        from ai_engine.tasks import process_university_content
        for obj in queryset:
            try:
                process_university_content.delay(obj.id)
            except Exception:
                process_university_content(obj.id)
        self.message_user(request, f"{queryset.count()} ta kontent AI ga yuborildi.")
    process_with_ai.short_description = "AI bilan qayta ishlash"