"""accounts/models.py"""
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email majburiy")
        email = self.normalize_email(email)
        user  = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email       = models.EmailField("Email", unique=True)
    first_name  = models.CharField("Ism",       max_length=100, blank=True)
    last_name   = models.CharField("Familiya",  max_length=100, blank=True)
    LANGUAGE_CHOICES = [
        ('uz', "O'zbek"),
        ('ru', 'Русский'),
        ('en', 'English'),
    ]
    THEME_CHOICES = [
        ('light', 'Kunduzgi'),
        ('dark',  'Tungi'),
    ]
    language    = models.CharField("Til",   max_length=5,  choices=LANGUAGE_CHOICES, default='uz')
    theme       = models.CharField("Mavzu", max_length=10, choices=THEME_CHOICES,    default='light')
    onboarded   = models.BooleanField("Onboarding o'tildi", default=False)

    GENDER_CHOICES = [
        ('male',   'Erkak'),
        ('female', 'Ayol'),
    ]
    gender      = models.CharField("Jins", max_length=10, choices=GENDER_CHOICES, blank=True)
    is_active   = models.BooleanField("Faol",   default=True)
    is_staff    = models.BooleanField("Xodim",  default=False)
    date_joined = models.DateTimeField("Qo'shilgan", default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name        = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email


SUBJECT_CHOICES = [
    ('math',      'Matematika'),   ('physics',   'Fizika'),
    ('chemistry', 'Kimyo'),        ('biology',   'Biologiya'),
    ('history',   'Tarix'),        ('geography', 'Geografiya'),
    ('english',   'Ingliz tili'),  ('russian',   'Rus tili'),
    ('lit',       'Adabiyot'),     ('cs',        'Informatika'),
]

LANGUAGE_CHOICES = [
    ('uz', "O'zbek"), ('ru', 'Rus'),     ('en', 'Ingliz'),
    ('de', 'Nemis'),  ('fr', 'Fransuz'), ('ko', 'Koreys'),
    ('zh', 'Xitoy'),  ('ja', 'Yapon'),  ('ar', 'Arab'),
]

DEGREE_CHOICES = [
    ('bachelor', 'Bakalavr'), ('master', 'Magistr'), ('phd', 'Doktorantura'),
]

STUDY_TYPE_CHOICES = [
    ('local', 'Mahalliy'), ('abroad', 'Xorijda'),
    ('both',  'Ikkalasi'), ('online', 'Online'),
]


class AbituriyentProfile(models.Model):
    user   = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField("Avatar", upload_to="avatars/", blank=True, null=True)

    # Akademik
    ielts_score       = models.FloatField("IELTS",               null=True, blank=True)
    sat_score         = models.PositiveIntegerField("SAT",       null=True, blank=True)
    gpa               = models.FloatField("GPA",                 null=True, blank=True)
    olympiad_level    = models.CharField("Olimpiada", max_length=20, blank=True,
                                          choices=[('school','Maktab'),('district','Tuman'),
                                                   ('regional','Viloyat'),('national','Respublika'),
                                                   ('international','Xalqaro')])

    # Yo'nalish
    main_subject      = models.CharField("Asosiy fan",    max_length=20, choices=SUBJECT_CHOICES, blank=True)
    second_subject    = models.CharField("Ikkinchi fan",  max_length=20, choices=SUBJECT_CHOICES, blank=True)
    desired_degree    = models.CharField("Daraja",        max_length=20, choices=DEGREE_CHOICES,  default='bachelor')
    desired_specialty = models.CharField("Mutaxassislik", max_length=255, blank=True)
    study_type        = models.CharField("O'qish turi",   max_length=20, choices=STUDY_TYPE_CHOICES, default='both')

    # Tillar
    native_language   = models.CharField("Ona til", max_length=5, choices=LANGUAGE_CHOICES, default='uz')
    language_skills   = models.JSONField("Til ko'nikmalari", default=list, blank=True)

    # Moliya
    can_self_finance  = models.BooleanField("O'zi to'lay oladi", default=False)
    needs_grant       = models.BooleanField("Grant kerak",       default=True)
    monthly_budget    = models.PositiveIntegerField("Oylik byudjet ($)", null=True, blank=True)

    # Qo'shimcha
    volunteer_hours      = models.PositiveIntegerField("Volontyor soat", default=0)
    has_work_experience  = models.BooleanField("Ish tajribasi",          default=False)
    work_experience_desc = models.TextField("Ish tajribasi tavsifi",     blank=True)
    essays_count         = models.PositiveIntegerField("Essay soni",     default=0)
    achievements         = models.TextField("Yutuqlar",                  blank=True)
    bio                  = models.TextField("Qisqacha tanishuv",         blank=True)

    profile_completed = models.BooleanField("Profil to'ldirilgan", default=False)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Abituriyent Profili"
        verbose_name_plural = "Abituriyent Profillari"

    def __str__(self):
        return f"{self.user.get_full_name()} — Profil"

    @property
    def completion_percent(self):
        fields = [
            self.gpa, self.main_subject,
            self.desired_specialty, self.study_type,
            self.user.first_name, self.user.last_name,
        ]
        filled = sum(1 for f in fields if f)
        return int((filled / len(fields)) * 100)

    def save(self, *args, **kwargs):
        self.profile_completed = self.completion_percent >= 70
        super().save(*args, **kwargs)


class PasswordResetOTP(models.Model):
    PURPOSE_CHOICES = [
        ('reset',  'Parol tiklash'),
        ('verify', 'Email tasdiqlash'),
    ]

    user       = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='otp_codes')
    code       = models.CharField(max_length=6)
    purpose    = models.CharField(
        "Maqsad", max_length=10,
        choices=PURPOSE_CHOICES, default='reset'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)

    class Meta:
        verbose_name        = "OTP Kod"
        verbose_name_plural = "OTP Kodlar"
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.user.email} — {self.code} ({self.purpose})"

    @property
    def is_expired(self):
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(minutes=15)