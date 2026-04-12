"""
core/models.py
Admin paneldan boshqariladigan sayt sozlamalari
"""
from django.db import models
from django.core.cache import cache
from django.utils import timezone


class SiteSettings(models.Model):
    """Saytning barcha global sozlamalari — faqat bitta obyekt"""

    # Branding
    name        = models.CharField("Sayt nomi", max_length=100, default="EduPath")
    short_name  = models.CharField("Qisqa nom (PWA)", max_length=30, default="EduPath")
    tagline     = models.CharField("Tagline", max_length=200, default="Kelajagingni Rejalashtir")
    logo        = models.ImageField("Logo", upload_to="site/", blank=True, null=True)
    favicon     = models.ImageField("Favicon", upload_to="site/", blank=True, null=True)

    # SEO
    meta_description = models.TextField("Meta description", max_length=300, blank=True)

    # Auth sahifa matnlari
    login_title       = models.CharField("Login sarlavha", max_length=100, default="Xush kelibsiz!")
    login_subtitle    = models.CharField("Login taglavha", max_length=200, default="Hisobingizga kiring")
    register_title    = models.CharField("Register sarlavha", max_length=100, default="Hisob yarating")
    register_subtitle = models.CharField("Register taglavha", max_length=200, default="Bepul ro'yxatdan o'ting")
    auth_hero_title   = models.CharField("Auth hero sarlavha", max_length=150, default="Kelajagingni Rejalashtir")
    auth_hero_sub     = models.CharField("Auth hero taglavha", max_length=200, default="O'z imkoniyatlaringni bil")

    # Aloqa
    official_email = models.EmailField("Rasmiy email", blank=True)
    phone          = models.CharField("Telefon", max_length=20, blank=True)
    address        = models.CharField("Manzil", max_length=255, blank=True)

    # Email sozlamalari (forgot password uchun)
    smtp_host     = models.CharField("SMTP Host", max_length=255, blank=True, default="smtp.gmail.com")
    smtp_port     = models.PositiveIntegerField("SMTP Port", default=587)
    smtp_email    = models.EmailField("SMTP Email", blank=True)
    smtp_password = models.CharField("SMTP Parol / App Password", max_length=255, blank=True)
    smtp_use_tls  = models.BooleanField("TLS ishlatish", default=True)

    # Ijtimoiy tarmoqlar
    telegram  = models.URLField("Telegram", blank=True)
    instagram = models.URLField("Instagram", blank=True)
    facebook  = models.URLField("Facebook", blank=True)
    youtube   = models.URLField("YouTube", blank=True)
    linkedin  = models.URLField("LinkedIn", blank=True)

    # Sozlamalar
    maintenance_mode = models.BooleanField("Ta'mirlash rejimi", default=False)
    allow_register   = models.BooleanField("Ro'yxatdan o'tishga ruxsat", default=True)

    class Meta:
        verbose_name        = "Sayt Sozlamalari"
        verbose_name_plural = "Sayt Sozlamalari"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete('site_settings')

    @classmethod
    def get(cls):
        cached = cache.get('site_settings')
        if cached:
            return cached
        obj, _ = cls.objects.get_or_create(pk=1)
        cache.set('site_settings', obj, 3600)
        return obj


class NavbarExtraLink(models.Model):
    """Drawer (yon menyu) ga qo'shimcha dinamik linklar"""
    name         = models.CharField("Nom", max_length=100)
    url          = models.CharField("URL", max_length=255)
    icon_svg     = models.TextField("SVG icon", blank=True)
    order        = models.PositiveIntegerField("Tartib", default=0)
    is_active    = models.BooleanField("Faol", default=True)
    open_new_tab = models.BooleanField("Yangi tabda ochish", default=False)

    class Meta:
        verbose_name        = "Drawer Extra Link"
        verbose_name_plural = "Drawer Extra Linklar"
        ordering            = ['order']

    def __str__(self):
        return self.name


class FooterSettings(models.Model):
    """Footer sozlamalari"""
    description    = models.TextField("Tavsif", blank=True)
    copyright_text = models.CharField(
        "Copyright matni", max_length=255,
        default="© 2025 EduPath. Barcha huquqlar himoyalangan."
    )

    class Meta:
        verbose_name        = "Footer Sozlamalari"
        verbose_name_plural = "Footer Sozlamalari"

    def __str__(self):
        return "Footer Sozlamalari"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


class FooterColumn(models.Model):
    """Footer ustunlari"""
    footer = models.ForeignKey(FooterSettings, on_delete=models.CASCADE, related_name='columns')
    title  = models.CharField("Ustun nomi", max_length=100)
    order  = models.PositiveIntegerField("Tartib", default=0)

    class Meta:
        verbose_name        = "Footer Ustuni"
        verbose_name_plural = "Footer Ustunlari"
        ordering            = ['order']

    def __str__(self):
        return self.title


class FooterLink(models.Model):
    """Footer ustunidagi linklar"""
    column       = models.ForeignKey(FooterColumn, on_delete=models.CASCADE, related_name='links')
    name         = models.CharField("Nom", max_length=100)
    url          = models.CharField("URL", max_length=255)
    order        = models.PositiveIntegerField("Tartib", default=0)
    open_new_tab = models.BooleanField("Yangi tabda ochish", default=False)

    class Meta:
        verbose_name        = "Footer Link"
        verbose_name_plural = "Footer Linklar"
        ordering            = ['order']

    def __str__(self):
        return self.name


class AISettings(models.Model):
    """AI provider sozlamalari — admin paneldan o'zgartiriladi"""

    PROVIDER_CHOICES = [
        ('claude',    'Anthropic Claude'),
        ('openai',    'OpenAI GPT'),
        ('gemini',    'Google Gemini'),
        ('deepseek',  'DeepSeek'),
        ('groq',      'Groq (Bepul)'),
    ]

    provider   = models.CharField("Provider", max_length=20, choices=PROVIDER_CHOICES, default='claude')
    api_key    = models.CharField("API Key", max_length=500)
    model_name = models.CharField(
        "Model nomi", max_length=100,
        help_text="Masalan: claude-3-5-sonnet-20241022, gpt-4o, gemini-pro"
    )
    max_tokens  = models.PositiveIntegerField("Max Tokens", default=2000)
    temperature = models.FloatField("Temperature", default=0.7)
    is_active   = models.BooleanField("Faol", default=True)
    notes       = models.TextField("Izoh", blank=True)

    class Meta:
        verbose_name        = "AI Sozlamalari"
        verbose_name_plural = "AI Sozlamalari"

    def __str__(self):
        return f"{self.get_provider_display()} — {self.model_name}"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete('ai_settings')

    @classmethod
    def get(cls):
        cached = cache.get('ai_settings')
        if cached:
            return cached
        obj = cls.objects.filter(is_active=True).first()
        if obj:
            cache.set('ai_settings', obj, 3600)
        return obj


class DrawerLink(models.Model):
    name         = models.CharField(max_length=100)
    url          = models.CharField(max_length=300)
    open_new_tab = models.BooleanField(default=False)
    order        = models.PositiveIntegerField(default=0)
    is_active    = models.BooleanField(default=True)

    class Meta:
        ordering            = ['order']
        verbose_name        = 'Drawer havolasi'
        verbose_name_plural = 'Drawer havolalari'

    def __str__(self):
        return self.name


class VideoLesson(models.Model):
    title       = models.CharField("Sarlavha", max_length=200)
    description = models.TextField("Tavsif", blank=True)
    video_url   = models.URLField(
        "Video URL",
        help_text='Bunny.net embed URL: https://iframe.mediadelivery.net/embed/{libraryId}/{videoId} '
                  'yoki YouTube URL ham qabul qilinadi'
    )
    # ✅ Admin paneldan yuklanadigan thumbnail
    thumbnail   = models.ImageField(
        "Thumbnail rasm",
        upload_to="videos/thumbnails/",
        blank=True,
        null=True,
        help_text="Ixtiyoriy. Bo'sh qoldirilsa, YouTube/Bunny.net dan avtomatik olinadi."
    )
    order       = models.PositiveIntegerField("Tartib", default=0)
    is_active   = models.BooleanField("Faol", default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['order']
        verbose_name        = 'Video dars'
        verbose_name_plural = 'Video darslar'

    def __str__(self):
        return f'{self.order}. {self.title}'

    @property
    def is_bunny(self):
        """Bunny.net video ekanligini tekshiradi"""
        return 'mediadelivery.net' in self.video_url or 'b-cdn.net' in self.video_url

    def get_embed_url(self):
        """Bunny.net yoki YouTube embed URL qaytaradi"""
        url = self.video_url

        # Bunny.net — to'g'ridan URL, kerakli parametrlar qo'shiladi
        if 'mediadelivery.net' in url:
            if '?' not in url:
                url += '?autoplay=false&preload=true'
            return url

        # YouTube short link
        if 'youtu.be/' in url:
            vid = url.split('youtu.be/')[-1].split('?')[0]
            return f'https://www.youtube.com/embed/{vid}'

        # YouTube watch link
        if 'youtube.com/watch' in url:
            import urllib.parse as up
            params = up.parse_qs(up.urlparse(url).query)
            vid = params.get('v', [''])[0]
            return f'https://www.youtube.com/embed/{vid}'

        # Allaqachon embed URL
        if 'youtube.com/embed/' in url:
            return url

        return url

    def get_thumbnail(self):
        """
        Thumbnail URL qaytaradi. Ustuvorlik tartibi:
        1. Admin paneldan yuklangan rasm (thumbnail field)
        2. YouTube avtomatik thumbnail
        3. Bunny.net CDN thumbnail
        4. Bo'sh string (fallback)
        """
        # 1. Admin yuklagan rasm mavjud bo'lsa — uni ishlatamiz
        if self.thumbnail:
            return self.thumbnail.url

        url = self.video_url

        # 2. YouTube thumbnail
        vid = None
        if 'youtu.be/' in url:
            vid = url.split('youtu.be/')[-1].split('?')[0]
        elif 'youtube.com/watch' in url:
            import urllib.parse as up
            params = up.parse_qs(up.urlparse(url).query)
            vid = params.get('v', [''])[0]
        elif 'youtube.com/embed/' in url:
            vid = url.split('youtube.com/embed/')[-1].split('?')[0]

        if vid:
            return f'https://img.youtube.com/vi/{vid}/mqdefault.jpg'

        # 3. Bunny.net thumbnail (ishlamasa ham frontendda onerror bilan yashiriladi)
        if 'mediadelivery.net/embed/' in url:
            parts = url.rstrip('/').split('/')
            video_id = parts[-1].split('?')[0]
            library_id = parts[-2]
            return f'https://vz-{library_id}.b-cdn.net/{video_id}/thumbnail.jpg'

        return ''


class VideoProgress(models.Model):
    user       = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='video_progress')
    video      = models.ForeignKey(VideoLesson, on_delete=models.CASCADE, related_name='progress')
    watched    = models.BooleanField(default=False)
    position   = models.FloatField(default=0, help_text='Seconds watched')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'video')
        verbose_name    = 'Video progress'

    def __str__(self):
        return f'{self.user} — {self.video}'