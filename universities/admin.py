"""universities/admin.py"""
from django.contrib import admin
from django.utils.html import format_html
from django.forms import BaseInlineFormSet
from django.core.exceptions import ValidationError
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


# ─── Inlines ─────────────────────────────────────────────────
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


# ─── Grant Choice Inline (Savol ichida) ──────────────────────
class GrantChoiceFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        correct = sum(
            1 for form in self.forms
            if form.cleaned_data and
               form.cleaned_data.get('is_correct') and
               not form.cleaned_data.get('DELETE', False)
        )
        total = sum(
            1 for form in self.forms
            if form.cleaned_data and
               not form.cleaned_data.get('DELETE', False)
        )
        if total > 0 and correct != 1:
            raise ValidationError("Har bir savolda aynan 1 ta to'g'ri javob bo'lishi kerak!")


class GrantChoiceInline(admin.TabularInline):
    model      = GrantChoice
    formset    = GrantChoiceFormSet
    extra      = 3
    min_num    = 3
    max_num    = 4
    fields     = ['text', 'is_correct', 'order']
    ordering   = ['order']


# ─── Grant Question Inline (Test ichida) ─────────────────────
class GrantQuestionInline(admin.StackedInline):
    model            = GrantQuestion
    extra            = 1
    fields           = ['text', 'order', 'explanation']
    show_change_link = True
    ordering         = ['order']


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
        ("Asosiy", {'fields': ('name', 'slug', 'country', 'city', 'grant_type', 'website',
                               'logo', 'logo_preview', 'cover_image', 'is_published')}),
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
    list_display        = ['name', 'grant_type_badge', 'country', 'degree',
                           'founded_year', 'amount', 'video_count', 'uni_count', 'is_active']
    list_filter         = ['grant_type', 'country', 'degree', 'is_active']
    search_fields       = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal   = ['universities']
    inlines             = [StandaloneGrantVideoInline]
    readonly_fields     = ['cover_preview', 'logo_preview']

    fieldsets = (
        ("Asosiy", {'fields': ('name', 'slug', 'grant_type', 'country', 'degree',
                               'logo', 'logo_preview', 'cover_image', 'cover_preview', 'is_active')}),
        ("Ma'lumotlar", {'fields': ('description', 'founded_year', 'directions', 'requirements', 'winners_count')}),
        ("Mukofot va muddat", {'fields': ('amount', 'deadline', 'deadline_text', 'min_ielts', 'min_gpa')}),
        ("Havolalar", {'fields': ('apply_url', 'official_site')}),
        ("Universitetlar (ixtiyoriy)", {
            'fields': ('universities',),
            'description': "Bo'sh qoldirilsa — umumiy grantlar ro'yxatida ko'rinadi."
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


# ─── Grant Test — bitta sahifada hammasi ─────────────────────
@admin.register(GrantTest)
class GrantTestAdmin(admin.ModelAdmin):
    list_display  = ['title', 'grant', 'question_count_display', 'time_limit', 'pass_percent', 'is_active']
    list_filter   = ['is_active']
    search_fields = ['title', 'grant__name']
    inlines       = [GrantQuestionInline]
    save_on_top   = True

    fieldsets = (
        ("1. Grant tanlang", {
            'fields': ('grant', 'is_active'),
            'description': "Qaysi grant uchun test yaratyapsiz?"
        }),
        ("2. Test sozlamalari", {
            'fields': ('title', 'description', 'time_limit', 'pass_percent'),
            'description': "Vaqt limiti 0 = cheklanmagan. O'tish foizi: masalan 60 = 60%"
        }),
    )

    def question_count_display(self, obj):
        cnt = obj.questions.count()
        return format_html('<span style="color:#2196F3;font-weight:600">{} ta savol</span>', cnt)
    question_count_display.short_description = "Savollar"

    def response_add(self, request, obj, post_url_continue=None):
        """Saqlash va davom etish — savol qo'shishga qaytadi"""
        if '_continue' in request.POST or '_addanother' not in request.POST:
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            return HttpResponseRedirect(
                reverse('admin:universities_granttest_change', args=[obj.pk])
            )
        return super().response_add(request, obj, post_url_continue)


# ─── Grant Savoli — variantlar bitta sahifada ─────────────────
@admin.register(GrantQuestion)
class GrantQuestionAdmin(admin.ModelAdmin):
    list_display  = ['text_short', 'test', 'order', 'choices_status']
    list_filter   = ['test']
    search_fields = ['text', 'test__title']
    inlines       = [GrantChoiceInline]
    save_on_top   = True

    fieldsets = (
        ("Savol", {
            'fields': ('test', 'text', 'order', 'explanation'),
            'description': "Savolni kiriting. Pastda variantlarni to'ldiring (min 3, max 4). Faqat 1 ta 'To'g'ri javob' belgilang."
        }),
    )

    def text_short(self, obj):
        return obj.text[:70] + '...' if len(obj.text) > 70 else obj.text
    text_short.short_description = "Savol"

    def choices_status(self, obj):
        cnt     = obj.choices.count()
        correct = obj.choices.filter(is_correct=True).count()
        if cnt == 0:
            return format_html('<span style="color:#f59e0b">⚠️ Variantlar yo\'q</span>')
        if correct != 1:
            return format_html('<span style="color:#ef4444">❌ To\'g\'ri javob: {} ta</span>', correct)
        return format_html('<span style="color:#10b981">✅ {} ta variant</span>', cnt)
    choices_status.short_description = "Variantlar holati"

    def response_add(self, request, obj, post_url_continue=None):
        """Saqlash va davom etish yoki yangi savol"""
        if '_addanother' in request.POST:
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            return HttpResponseRedirect(
                reverse('admin:universities_grantquestion_add') +
                f'?test={obj.test.pk}'
            )
        if '_continue' in request.POST:
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            return HttpResponseRedirect(
                reverse('admin:universities_grantquestion_change', args=[obj.pk])
            )
        return super().response_add(request, obj, post_url_continue)

    def get_changeform_initial_data(self, request):
        """URL dan test_id olish — yangi savol qo'shganda test avtomatik tanlanadi"""
        initial = super().get_changeform_initial_data(request)
        test_id = request.GET.get('test')
        if test_id:
            initial['test'] = test_id
        return initial


# ─── Test Natijalari ─────────────────────────────────────────
@admin.register(GrantTestResult)
class GrantTestResultAdmin(admin.ModelAdmin):
    list_display    = ['user', 'test', 'score_display', 'time_display', 'passed_display', 'created_at']
    list_filter     = ['test', 'created_at']
    search_fields   = ['user__email', 'test__title']
    readonly_fields = ['user', 'test', 'score', 'total', 'time_spent', 'answers', 'created_at']

    def score_display(self, obj):
        color = '#10b981' if obj.is_passed else '#ef4444'
        return format_html(
            '<span style="color:{};font-weight:700">{}/{} ({}%)</span>',
            color, obj.score, obj.total, obj.percent
        )
    score_display.short_description = "Natija"

    def time_display(self, obj):
        return f"⏱ {obj.time_spent_display}"
    time_display.short_description = "Vaqt"

    def passed_display(self, obj):
        if obj.is_passed:
            return format_html('<span style="color:#10b981;font-weight:600">✅ O\'tdi</span>')
        return format_html('<span style="color:#ef4444;font-weight:600">❌ O\'tmadi</span>')
    passed_display.short_description = "Holat"