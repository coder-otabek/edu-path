"""accounts/admin.py"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, AbituriyentProfile, PasswordResetOTP


class ProfileInline(admin.StackedInline):
    model  = AbituriyentProfile
    extra  = 0
    fields = [
        'avatar', 'ielts_score', 'sat_score', 'gpa',
        'main_subject', 'desired_specialty', 'study_type',
        'needs_grant', 'volunteer_hours', 'profile_completed',
    ]


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    inlines          = [ProfileInline]
    list_display     = ['email', 'first_name', 'last_name', 'gender', 'is_active', 'date_joined']
    list_filter      = ['is_active', 'is_staff', 'date_joined']
    search_fields    = ['email', 'first_name', 'last_name']
    ordering         = ['-date_joined']
    fieldsets        = (
        (None,           {'fields': ('email', 'password')}),
        ('Shaxsiy',      {'fields': ('first_name', 'last_name', 'gender')}),

        ('Ruxsatlar',    {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Sanalar',      {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets    = (
        (None, {
            'classes': ('wide',),
            'fields':  ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    readonly_fields  = ['last_login', 'date_joined']


@admin.register(AbituriyentProfile)
class AbituriyentProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'gpa', 'study_type', 'profile_completed']
    list_filter   = ['study_type', 'profile_completed', 'needs_grant']
    search_fields = ['user__email', 'user__first_name', 'desired_specialty']


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'created_at', 'is_used']
    list_filter  = ['is_used']
    readonly_fields = ['user', 'code', 'created_at']