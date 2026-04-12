"""
core/middleware.py
"""
from django.shortcuts import render


class MaintenanceModeMiddleware:
    """Admin paneldan ta'mirlash rejimini yoqish/o'chirish"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Admin va static fayllarni o'tkazib yuborish
        exempt_paths = ['/admin/', '/static/', '/media/']
        if any(request.path.startswith(p) for p in exempt_paths):
            return self.get_response(request)

        # Superuser o'tishi mumkin
        if request.user.is_authenticated and request.user.is_superuser:
            return self.get_response(request)

        try:
            from core.models import SiteSettings
            site = SiteSettings.get()
            if site and site.maintenance_mode:
                return render(request, 'core/maintenance.html', {'site': site}, status=503)
        except Exception:
            pass

        return self.get_response(request)


class OnboardingMiddleware:
    """Yangi foydalanuvchilarni onboarding sahifasiga yo'naltiradi"""
    EXEMPT = [
        '/',
        '/accounts/onboarding/',
        '/accounts/login/',
        '/accounts/register/',
        '/accounts/logout/',
        '/accounts/forgot-password/',
        '/accounts/otp-verify/',
        '/accounts/reset-password/',
        '/admin/',
        '/static/',
        '/media/',
        '/manifest.json',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (request.user.is_authenticated
                and not request.user.onboarded
                and not any(request.path.startswith(p) for p in self.EXEMPT)):
            from django.shortcuts import redirect
            return redirect('/accounts/onboarding/')
        return self.get_response(request)