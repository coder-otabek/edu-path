"""accounts/urls.py"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/',        views.register_view,       name='register'),
    path('login/',           views.login_view,           name='login'),
    path('logout/',          views.logout_view,          name='logout'),

    # Parol tiklash
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('otp-verify/',      views.otp_verify_view,      name='otp_verify'),
    path('reset-password/',  views.reset_password_view,  name='reset_password'),

    # Email tasdiqlash (ro'yxatdan o'tish)
    path('email-verify/',    views.email_verify_view,    name='email_verify'),

    # Profil
    path('profile/',         views.profile_view,         name='profile'),
    path('profile/edit/',    views.profile_edit_view,    name='profile_edit'),
    path('settings/',        views.settings_view,        name='settings'),
    path('onboarding/',      views.onboarding_view,      name='onboarding'),
]