"""dashboard/models.py — Essay modeli"""
from django.db import models
from accounts.models import CustomUser


class Essay(models.Model):
    TYPE_CHOICES = [
        ('motivation', 'Motivatsiya xati'),
        ('personal',   'Personal Statement'),
        ('scholarship','Stipendiya essay'),
        ('why_us',     "Nima uchun bu universitet"),
        ('other',      'Boshqa'),
    ]
    STATUS_CHOICES = [
        ('draft',     'Qoralama'),
        ('submitted', 'Yuborildi'),
        ('reviewed',  'Baholandi'),
    ]

    user        = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='essays')
    title       = models.CharField("Sarlavha", max_length=255)
    essay_type  = models.CharField("Tur", max_length=20, choices=TYPE_CHOICES, default='motivation')
    content     = models.TextField("Matn", blank=True)
    file        = models.FileField("Fayl", upload_to="essays/", blank=True, null=True)
    status      = models.CharField("Holat", max_length=20, choices=STATUS_CHOICES, default='draft')
    word_count  = models.PositiveIntegerField("So'z soni", default=0)

    # AI baholash
    ai_score        = models.FloatField("AI ball", null=True, blank=True)
    ai_feedback     = models.TextField("AI fikr", blank=True)
    ai_strengths    = models.TextField("Kuchli tomonlar", blank=True)
    ai_weaknesses   = models.TextField("Zaif tomonlar", blank=True)
    ai_suggestions  = models.TextField("Tavsiyalar", blank=True)
    ai_reviewed_at  = models.DateTimeField("AI baholagan vaqt", null=True, blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Essay"
        verbose_name_plural = "Essaylar"
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.title}"

    def save(self, *args, **kwargs):
        if self.content:
            self.word_count = len(self.content.split())
        super().save(*args, **kwargs)


class VolunteerActivity(models.Model):
    user         = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='volunteer_activities')
    organization = models.CharField("Tashkilot nomi", max_length=255)
    role         = models.CharField("Vazifa/Rol", max_length=255)
    description  = models.TextField("Tavsif", blank=True)
    hours        = models.PositiveIntegerField("Soat soni")
    start_date   = models.DateField("Boshlangan sana")
    end_date     = models.DateField("Tugagan sana", null=True, blank=True)
    is_ongoing   = models.BooleanField("Davom etmoqda", default=False)
    certificate  = models.FileField("Sertifikat", upload_to="volunteer/certs/", blank=True, null=True)

    # AI tavsiyasi
    ai_cv_text   = models.TextField("AI CV matni", blank=True)

    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Volontyor Faoliyat"
        verbose_name_plural = "Volontyor Faoliyatlar"
        ordering            = ['-start_date']

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.organization}"

    @property
    def date_range(self):
        end = "hozir" if self.is_ongoing else (str(self.end_date) if self.end_date else "—")
        return f"{self.start_date} — {end}"