"""universities/models.py"""
from django.db import models
from django.utils.text import slugify
import uuid

# ─── Choices ────────────────────────────────────────────────
GRANT_TYPE_CHOICES = [
    ('foreign', 'Xorijiy grant'),
    ('local',   'Mahalliy grant'),
    ('both',    'Ikkalasi ham'),
]

COUNTRY_CHOICES = [
    ('uz', "O'zbekiston"),
    ('us', 'AQSh'),
    ('uk', 'Buyuk Britaniya'),
    ('de', 'Germaniya'),
    ('kr', 'Janubiy Koreya'),
    ('cn', 'Xitoy'),
    ('ru', 'Rossiya'),
    ('fr', 'Fransiya'),
    ('jp', 'Yaponiya'),
    ('ae', 'BAA'),
    ('tr', 'Turkiya'),
    ('ca', 'Kanada'),
    ('au', 'Avstraliya'),
    ('other', 'Boshqa'),
]

DEGREE_CHOICES = [
    ('bachelor', 'Bakalavr'),
    ('master',   'Magistr'),
    ('phd',      'Doktorantura'),
    ('all',      'Barcha darajalar'),
]


# ─── Mutaxassislik ──────────────────────────────────────────
class Specialty(models.Model):
    name = models.CharField("Mutaxassislik nomi", max_length=255)

    class Meta:
        verbose_name        = "Mutaxassislik"
        verbose_name_plural = "Mutaxassisliklar"
        ordering            = ['name']

    def __str__(self):
        return self.name


# ─── Universitet ─────────────────────────────────────────────
class University(models.Model):
    name        = models.CharField("Universitet nomi", max_length=255)
    slug        = models.SlugField(max_length=255, unique=True, blank=True)
    logo        = models.ImageField("Logotip", upload_to="universities/logos/", blank=True, null=True)
    cover_image = models.ImageField("Muqova rasm", upload_to="universities/covers/", blank=True, null=True)
    country     = models.CharField("Mamlakat", max_length=10, choices=COUNTRY_CHOICES, default='uz')
    city        = models.CharField("Shahar", max_length=100, blank=True)
    grant_type  = models.CharField("Grant turi", max_length=10, choices=GRANT_TYPE_CHOICES, default='foreign')

    website     = models.URLField("Rasmiy sayt", blank=True)
    description = models.TextField("Tavsif", blank=True)
    ai_summary  = models.TextField("AI xulosasi", blank=True)

    min_ielts_score  = models.FloatField("Min IELTS", null=True, blank=True)
    min_sat_score    = models.PositiveIntegerField("Min SAT", null=True, blank=True)
    min_gpa          = models.FloatField("Min GPA", null=True, blank=True)
    tuition_fee_min  = models.PositiveIntegerField("Min to'lov ($/yil)", null=True, blank=True)
    tuition_fee_max  = models.PositiveIntegerField("Max to'lov ($/yil)", null=True, blank=True)
    has_grant        = models.BooleanField("Grant mavjud", default=True)
    specialties      = models.ManyToManyField(Specialty, blank=True, verbose_name="Yo'nalishlar")
    is_published     = models.BooleanField("E'lon qilingan", default=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Universitet"
        verbose_name_plural = "Universitetlar"
        ordering            = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n    = 1
            while University.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n   += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('universities:detail', kwargs={'slug': self.slug})


# ─── Universitet Grant ───────────────────────────────────────
class Grant(models.Model):
    university    = models.ForeignKey(
        University, on_delete=models.CASCADE,
        related_name='grants', verbose_name="Universitet"
    )
    name          = models.CharField("Grant nomi", max_length=255)
    slug          = models.SlugField(max_length=255, blank=True)
    grant_type    = models.CharField("Grant turi", max_length=10, choices=GRANT_TYPE_CHOICES, default='foreign')
    degree        = models.CharField("Daraja", max_length=20, choices=DEGREE_CHOICES, default='bachelor')
    description   = models.TextField("Tavsif", blank=True)
    amount        = models.CharField("Miqdor", max_length=100, blank=True,
                                     help_text="Masalan: To'liq, 50%, $5000/yil")
    deadline      = models.DateField("Ariza topshirish muddati", null=True, blank=True)
    deadline_text = models.CharField("Muddat matni", max_length=100, blank=True,
                                     help_text="Masalan: Har yili May oxiri")
    min_ielts     = models.FloatField("Min IELTS", null=True, blank=True)
    min_gpa       = models.FloatField("Min GPA", null=True, blank=True)
    requirements  = models.TextField("Qo'shimcha talablar", blank=True)
    apply_url     = models.URLField("Ariza sahifasi", blank=True)
    is_active     = models.BooleanField("Faol", default=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Grant (Universitet)"
        verbose_name_plural = "Grantlar (Universitet)"
        ordering            = ['name']

    def __str__(self):
        return f"{self.university.name} — {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or str(uuid.uuid4())[:8]
            slug = base
            n    = 1
            while Grant.objects.filter(slug=slug, university=self.university).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n   += 1
            self.slug = slug
        super().save(*args, **kwargs)


# ─── Grant Video (Universitet granti uchun) ──────────────────
def grant_video_upload_path(instance, filename):
    return f"universities/grant_videos/{instance.grant.id}/{filename}"


class GrantVideo(models.Model):
    grant        = models.ForeignKey(
        Grant, on_delete=models.CASCADE,
        related_name='videos', verbose_name="Grant"
    )
    title        = models.CharField("Sarlavha", max_length=255)
    description  = models.TextField("Tavsif", blank=True)
    order        = models.PositiveSmallIntegerField("Tartib", default=0)
    video_file   = models.FileField("Video fayl", upload_to=grant_video_upload_path, blank=True, null=True)
    youtube_url  = models.URLField("YouTube havolasi", blank=True,
                                   help_text="https://youtube.com/watch?v=... yoki https://youtu.be/...")
    duration     = models.CharField("Davomiyligi", max_length=20, blank=True)
    thumbnail    = models.ImageField("Muqova rasm", upload_to="universities/video_thumbs/", blank=True, null=True)
    is_published = models.BooleanField("E'lon qilingan", default=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Grant Video"
        verbose_name_plural = "Grant Videolar"
        ordering            = ['grant', 'order']

    def __str__(self):
        return f"{self.grant.name} | {self.title}"


# ─── Mustaqil Grant ──────────────────────────────────────────
class StandaloneGrant(models.Model):
    name          = models.CharField("Grant nomi", max_length=255)
    slug          = models.SlugField(max_length=255, unique=True, blank=True)
    cover_image   = models.ImageField("Muqova rasm", upload_to="grants/covers/", blank=True, null=True)
    logo          = models.ImageField("Logotip / Bayroq", upload_to="grants/logos/", blank=True, null=True)
    grant_type    = models.CharField("Grant turi", max_length=10, choices=GRANT_TYPE_CHOICES, default='foreign')
    country       = models.CharField("Mamlakat", max_length=10, choices=COUNTRY_CHOICES, default='uz')
    degree        = models.CharField("Daraja", max_length=20, choices=DEGREE_CHOICES, default='all')
    description   = models.TextField("Tavsif", blank=True)
    directions    = models.TextField("Yo'nalishlar", blank=True)
    requirements  = models.TextField("Talablar", blank=True)
    amount        = models.CharField("Mukofot miqdori", max_length=255, blank=True)
    deadline      = models.DateField("Ariza muddati", null=True, blank=True)
    deadline_text = models.CharField("Muddat matni", max_length=100, blank=True)
    min_ielts     = models.FloatField("Min IELTS", null=True, blank=True)
    min_gpa       = models.FloatField("Min GPA", null=True, blank=True)
    universities  = models.ManyToManyField(University, blank=True, related_name='standalone_grants')
    apply_url     = models.URLField("Ariza sahifasi", blank=True)
    is_active     = models.BooleanField("Faol", default=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Mustaqil Grant"
        verbose_name_plural = "Mustaqil Grantlar"
        ordering            = ['grant_type', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ─── Mustaqil Grant Video ─────────────────────────────────────
def standalone_grant_video_path(instance, filename):
    return f"grants/videos/{instance.grant.id}/{filename}"


class StandaloneGrantVideo(models.Model):
    grant        = models.ForeignKey(
        StandaloneGrant, on_delete=models.CASCADE,
        related_name='videos', verbose_name="Grant"
    )
    title        = models.CharField("Sarlavha", max_length=255)
    description  = models.TextField("Tavsif", blank=True)
    order        = models.PositiveSmallIntegerField("Tartib", default=0)
    video_file   = models.FileField("Video fayl", upload_to=standalone_grant_video_path, blank=True, null=True)
    youtube_url  = models.URLField("YouTube havolasi", blank=True)
    duration     = models.CharField("Davomiyligi", max_length=20, blank=True)
    is_published = models.BooleanField("E'lon qilingan", default=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Mustaqil Grant Video"
        verbose_name_plural = "Mustaqil Grant Videolar"
        ordering            = ['grant', 'order']

    def __str__(self):
        return f"{self.grant.name} | {self.title}"


# ─── Universitet Kontent ─────────────────────────────────────
class UniversityContent(models.Model):
    university   = models.ForeignKey(University, on_delete=models.CASCADE, related_name='contents')
    title        = models.CharField("Sarlavha", max_length=255)
    content_type = models.CharField(max_length=10, choices=[('pdf', 'PDF'), ('text', 'Matn')])
    file         = models.FileField(upload_to="universities/content/", blank=True, null=True)
    text_content = models.TextField(blank=True)
    ai_processed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.university.name} — {self.title}"


# ─── Esse Namunasi ──────────────────────────────────────────
class EssaySample(models.Model):
    title       = models.CharField("Sarlavha", max_length=255)
    university  = models.ForeignKey(University, on_delete=models.SET_NULL, null=True, blank=True)
    content     = models.TextField("Esse matni")
    score       = models.IntegerField(default=5)
    is_active   = models.BooleanField(default=True)

    def __str__(self):
        return self.title


# ─── Grant Test (TO'G'RILANGAN QISM) ─────────────────────────
class GrantTest(models.Model):
    video        = models.OneToOneField(
        StandaloneGrantVideo, 
        on_delete=models.CASCADE,
        related_name='test', 
        verbose_name="Video dars",
        null=True,   # <-- Migratsiya xatosini oldini olish uchun
        blank=True   # <-- Migratsiya xatosini oldini olish uchun
    )
    title        = models.CharField("Test sarlavhasi", max_length=255)
    description  = models.TextField("Tavsif", blank=True)
    time_limit   = models.PositiveSmallIntegerField("Vaqt limiti (daqiqa)", default=10)
    pass_percent = models.PositiveSmallIntegerField("O'tish foizi (%)", default=60)
    is_active    = models.BooleanField("Faol", default=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Grant Testi"
        verbose_name_plural = "Grant Testlari"

    def __str__(self):
        try:
            return f"{self.video.grant.name} | {self.title}"
        except:
            return self.title


# ─── Test Savoli ─────────────────────────────────────────────
class GrantQuestion(models.Model):
    test         = models.ForeignKey(GrantTest, on_delete=models.CASCADE, related_name='questions')
    text         = models.TextField("Savol matni")
    order        = models.PositiveSmallIntegerField("Tartib", default=0)
    explanation  = models.TextField("Tushuntirish", blank=True)

    class Meta:
        verbose_name        = "Test Savoli"
        verbose_name_plural = "Test Savollari"
        ordering            = ['test', 'order']

    def __str__(self):
        return self.text[:60]


# ─── Javob Varianti ──────────────────────────────────────────
class GrantChoice(models.Model):
    question     = models.ForeignKey(GrantQuestion, on_delete=models.CASCADE, related_name='choices')
    text         = models.CharField("Variant matni", max_length=500)
    is_correct   = models.BooleanField("To'g'ri javob", default=False)
    order        = models.PositiveSmallIntegerField("Tartib", default=0)

    class Meta:
        verbose_name        = "Javob Varianti"
        verbose_name_plural = "Javob Variantlari"
        ordering            = ['question', 'order']

    def __str__(self):
        return self.text[:60]


# ─── Test Natijasi ────────────────────────────────────────────
class GrantTestResult(models.Model):
    user         = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='test_results')
    test         = models.ForeignKey(GrantTest, on_delete=models.CASCADE, related_name='results')
    score        = models.PositiveSmallIntegerField("To'g'ri javoblar soni", default=0)
    total        = models.PositiveSmallIntegerField("Jami savollar", default=0)
    time_spent   = models.PositiveIntegerField("Sarflangan vaqt (soniya)", default=0)
    created_at   = models.DateTimeField(auto_now_add=True)

    @property
    def percent(self):
        return round((self.score / self.total) * 100) if self.total else 0

    def __str__(self):
        return f"{self.user.email} — {self.percent}%"
