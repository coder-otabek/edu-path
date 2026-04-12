"""
core/email_backend.py
Admin paneldagi SiteSettings dan SMTP sozlamalarini dinamik o'qiydi
"""
from django.core.mail.backends.smtp import EmailBackend


class DynamicSMTPBackend(EmailBackend):
    """
    SiteSettings modelidan SMTP sozlamalarini o'qib,
    standart Django SMTP backendini sozlaydi.
    """

    def __init__(self, *args, **kwargs):
        # Import bu yerda — circular import oldini olish uchun
        try:
            from core.models import SiteSettings
            site = SiteSettings.get()
            kwargs.setdefault('host',       site.smtp_host or 'smtp.gmail.com')
            kwargs.setdefault('port',       site.smtp_port or 587)
            kwargs.setdefault('username',   site.smtp_email or '')
            kwargs.setdefault('password',   site.smtp_password or '')
            kwargs.setdefault('use_tls',    site.smtp_use_tls)
            kwargs.setdefault('fail_silently', False)
        except Exception:
            # Agar DB tayyor bo'lmasa — default qiymatlar
            kwargs.setdefault('host',       'smtp.gmail.com')
            kwargs.setdefault('port',       587)
            kwargs.setdefault('use_tls',    True)
            kwargs.setdefault('fail_silently', True)

        super().__init__(*args, **kwargs)
