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
    official_site = models.URLField("Rasmiy sayt", blank=True)
    order         = models.PositiveIntegerField("Tartib raqami", default=0,
                                                help_text="Kichik raqam — ro'yxatda yuqorida turadi")
    is_active     = models.BooleanField("Faol", default=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Mustaqil Grant"
        verbose_name_plural = "Mustaqil Grantlar"
        ordering            = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or str(uuid.uuid4())[:8]
            slug = base
            n    = 1
            while StandaloneGrant.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n   += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('universities:standalone_grant_detail', kwargs={'slug': self.slug})

    @property
    def directions_list(self):
        return [d.strip() for d in self.directions.splitlines() if d.strip()]

    @property
    def requirements_list(self):
        return [r.strip() for r in self.requirements.splitlines() if r.strip()]


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
    thumbnail    = models.ImageField("Muqova rasm", upload_to="grants/video_thumbs/", blank=True, null=True)
    is_published = models.BooleanField("E'lon qilingan", default=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Mustaqil Grant Video"
        verbose_name_plural = "Mustaqil Grant Videolar"
        ordering            = ['grant', 'order']

    def __str__(self):
        return f"{self.grant.name} | {self.title}"

    @property
    def youtube_embed_url(self):
        if not self.youtube_url:
            return ""
        url = self.youtube_url.strip()
        if "youtu.be/" in url:
            vid = url.split("youtu.be/")[-1].split("?")[0]
            return f"https://www.youtube.com/embed/{vid}"
        if "watch?v=" in url:
            vid = url.split("watch?v=")[-1].split("&")[0]
            return f"https://www.youtube.com/embed/{vid}"
        if "youtube.com/embed/" in url:
            return url
        return url

    @property
    def get_thumbnail(self):
        # 1. Admin yuklagan rasm
        if self.thumbnail:
            return self.thumbnail.url
        url = self.youtube_url or ''
        # 2. Bunny.net thumbnail
        if 'mediadelivery.net/embed/' in url:
            parts    = url.rstrip('/').split('/')
            video_id = parts[-1].split('?')[0]
            return f'https://vz-0b8beaf2-b26.b-cdn.net/{video_id}/thumbnail.jpg'
        # 3. YouTube thumbnail
        if 'youtu' in url:
            vid = None
            if 'youtu.be/' in url:
                vid = url.split('youtu.be/')[-1].split('?')[0]
            elif 'watch?v=' in url:
                vid = url.split('watch?v=')[-1].split('&')[0]
            elif 'youtube.com/embed/' in url:
                vid = url.split('youtube.com/embed/')[-1].split('?')[0]
            if vid:
                return f'https://img.youtube.com/vi/{vid}/mqdefault.jpg'
        return ''

    @property
    def has_video(self):
        return bool(self.video_file or self.youtube_url)


# ─── Universitet Kontent ─────────────────────────────────────
class UniversityContent(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('pdf',   'PDF hujjat'),
        ('docx',  'Word hujjat'),
        ('image', 'Rasm'),
        ('text',  'Matn'),
        ('audio', 'Audio'),
        ('video', 'Video'),
    ]
    university   = models.ForeignKey(
        University, on_delete=models.CASCADE,
        related_name='contents', verbose_name="Universitet"
    )
    title        = models.CharField("Sarlavha", max_length=255)
    content_type = models.CharField("Tur", max_length=10, choices=CONTENT_TYPE_CHOICES)
    file         = models.FileField("Fayl", upload_to="universities/content/", blank=True, null=True)
    text_content = models.TextField("Matn", blank=True)
    ai_extracted = models.TextField("AI ajratgan matn", blank=True)
    ai_summary   = models.TextField("AI xulosasi", blank=True)
    ai_processed = models.BooleanField("AI qayta ishladi", default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Universitet Kontent"
        verbose_name_plural = "Universitet Kontentlar"

    def __str__(self):
        return f"{self.university.name} — {self.title}"


# ─── Esse Namunasi ──────────────────────────────────────────
ESSAY_TYPE_CHOICES = [
    ('why_us',          "Nega bu universitet?"),
    ('personal_stmt',   "Shaxsiy bayonot"),
    ('motivation',      "Motivatsiya xati"),
    ('scholarship',     "Grant uchun esse"),
    ('extracurricular', "Qo'shimcha faoliyat"),
    ('challenge',       "Hayotiy qiyinchilik"),
    ('achievement',     "Yutuq haqida"),
    ('general',         "Umumiy esse"),
]

ESSAY_SCORE_CHOICES = [
    (5, "A'lo (namuna)"),
    (4, "Yaxshi"),
    (3, "O'rtacha"),
]


class EssaySample(models.Model):
    title       = models.CharField("Sarlavha", max_length=255)
    essay_type  = models.CharField("Esse turi", max_length=30, choices=ESSAY_TYPE_CHOICES, default='general')
    university  = models.ForeignKey(
        University, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='essay_samples',
        verbose_name="Universitet (ixtiyoriy)"
    )
    content     = models.TextField("Esse matni")
    score       = models.PositiveSmallIntegerField("Namuna sifati", choices=ESSAY_SCORE_CHOICES, default=5)
    structure_notes = models.TextField("Struktura izohi", blank=True)
    word_count  = models.PositiveIntegerField("So'z soni", default=0)
    language    = models.CharField("Til", max_length=5,
                                   choices=[('en', 'Ingliz'), ('uz', "O'zbek"), ('ru', 'Rus')],
                                   default='en')
    is_active   = models.BooleanField("Faol (AI uchun ishlatiladi)", default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Esse Namunasi"
        verbose_name_plural = "Esse Namunalari"
        ordering            = ['-score', 'essay_type']

    def __str__(self):
        return f"[{self.get_essay_type_display()}] {self.title} ({self.score})"

    def save(self, *args, **kwargs):
        if self.content:
            self.word_count = len(self.content.split())
        super().save(*args, **kwargs)


# ─── Grant Test ──────────────────────────────────────────────
class GrantTest(models.Model):
    video        = models.OneToOneField(
        StandaloneGrantVideo, on_delete=models.CASCADE,
        related_name='test', verbose_name="Video dars",
        null=True, blank=True
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
        except Exception:
            return self.title

    @property
    def question_count(self):
        return self.questions.count()

    @property
    def max_score(self):
        return self.questions.count()


# ─── Test Savoli ─────────────────────────────────────────────
class GrantQuestion(models.Model):
    test         = models.ForeignKey(
        GrantTest, on_delete=models.CASCADE,
        related_name='questions', verbose_name="Test"
    )
    text         = models.TextField("Savol matni")
    order        = models.PositiveSmallIntegerField("Tartib", default=0)
    explanation  = models.TextField("Tushuntirish", blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Test Savoli"
        verbose_name_plural = "Test Savollari"
        ordering            = ['test', 'order']

    def __str__(self):
        return f"{self.test.title} — {self.text[:60]}"


# ─── Javob Varianti ──────────────────────────────────────────
class GrantChoice(models.Model):
    question     = models.ForeignKey(
        GrantQuestion, on_delete=models.CASCADE,
        related_name='choices', verbose_name="Savol"
    )
    text         = models.CharField("Variant matni", max_length=500)
    is_correct   = models.BooleanField("To'g'ri javob", default=False)
    order        = models.PositiveSmallIntegerField("Tartib", default=0)

    class Meta:
        verbose_name        = "Javob Varianti"
        verbose_name_plural = "Javob Variantlari"
        ordering            = ['question', 'order']

    def __str__(self):
        mark = "✅" if self.is_correct else "❌"
        return f"{mark} {self.text[:60]}"


# ─── Test Natijasi ────────────────────────────────────────────
class GrantTestResult(models.Model):
    user         = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.CASCADE,
        related_name='test_results', verbose_name="Foydalanuvchi"
    )
    test         = models.ForeignKey(
        GrantTest, on_delete=models.CASCADE,
        related_name='results', verbose_name="Test"
    )
    score        = models.PositiveSmallIntegerField("To'g'ri javoblar soni", default=0)
    total        = models.PositiveSmallIntegerField("Jami savollar", default=0)
    time_spent   = models.PositiveIntegerField("Sarflangan vaqt (soniya)", default=0)
    answers      = models.JSONField("Javoblar", default=dict)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Test Natijasi"
        verbose_name_plural = "Test Natijalari"
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.user.email} — {self.percent}%"

    @property
    def percent(self):
        if not self.total:
            return 0
        return round((self.score / self.total) * 100)

    @property
    def is_passed(self):
        return self.percent >= self.test.pass_percent

    @property
    def grade(self):
        p = self.percent
        if p >= 90: return "A'lo"
        if p >= 75: return "Yaxshi"
        if p >= 60: return "Qoniqarli"
        return "Qoniqarsiz"

    @property
    def time_spent_display(self):
        m = self.time_spent // 60
        s = self.time_spent % 60
        return f"{m}:{s:02d}"