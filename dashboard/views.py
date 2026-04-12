import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from accounts.models import AbituriyentProfile
from universities.models import University
from ai_engine.models import RoadMap
from .models import Essay, VolunteerActivity


def _translate_tip(tip: str, user_lang: str) -> str:
    """ai_tip ni foydalanuvchi tiliga tarjima qilish (faqat til mos kelmasa)"""
    if not tip:
        return tip

    # Til aniqlash — sodda heuristika
    # Ruscha harflar ko'p bo'lsa — ruscha, o'zbekcha bo'lsa — o'zbekcha
    ru_chars = sum(1 for c in tip if '\u0400' <= c <= '\u04FF')
    total    = len(tip)
    is_ru    = ru_chars / total > 0.3 if total else False
    is_en    = all(ord(c) < 128 or c in ' .,!?-\n' for c in tip if c.strip())

    # Agar til allaqachon to'g'ri bo'lsa — tarjima kerak emas
    if user_lang == 'ru' and is_ru:
        return tip
    if user_lang == 'en' and is_en:
        return tip
    if user_lang == 'uz' and not is_ru and not is_en:
        return tip

    lang_map = {
        'uz': "o'zbek tilida (lotin alifbosida)",
        'ru': 'на русском языке',
        'en': 'in English',
    }
    lang_instr = lang_map.get(user_lang, "o'zbek tilida")

    try:
        from ai_engine.services import get_ai_response
        translated = get_ai_response([{
            "role": "user",
            "content": (
                f"Translate the following text {lang_instr}. "
                f"Keep it short, natural, and motivational. "
                f"Return ONLY the translated text, nothing else:\n\n{tip}"
            )
        }])
        return translated.strip()
    except Exception:
        return tip


@login_required
def home_view(request):
    profile, _ = AbituriyentProfile.objects.get_or_create(user=request.user)
    hour = timezone.localtime().hour
    if hour < 12:
        greeting = "Xayrli tong"
        greeting_key = "morning"
    elif hour < 17:
        greeting = "Xayrli kun"
        greeting_key = "afternoon"
    else:
        greeting = "Xayrli kech"
        greeting_key = "evening"

    all_unis    = University.objects.filter(is_published=True)
    total_unis  = all_unis.count()
    recommended = []
    if profile.profile_completed:
        qs = all_unis
        if profile.gpa:
            qs = qs.filter(min_gpa__lte=profile.gpa)
        recommended = list(qs.order_by('?')[:4])
    if not recommended:
        recommended = list(all_unis.order_by('?')[:4])

    roadmap = RoadMap.objects.filter(user=request.user).first()
    progress, ai_tip = 0, None
    if roadmap and roadmap.content:
        steps    = roadmap.content.get('steps', [])
        done     = sum(1 for s in steps if s.get('status') == 'done')
        progress = int((done / len(steps)) * 100) if steps else 0
        tips     = roadmap.content.get('tips', [])
        raw_tip  = tips[0] if tips else None

        # Foydalanuvchi tiliga moslab tarjima qilamiz
        if raw_tip:
            user_lang = getattr(request.user, 'language', 'uz') or 'uz'
            ai_tip = _translate_tip(raw_tip, user_lang)

    return render(request, 'dashboard/home.html', {
        'profile':                  profile,
        'greeting':                 greeting,
        'greeting_key':             greeting_key,
        'recommended_universities': recommended,
        'roadmap_progress':         progress,
        'ai_tip':                   ai_tip,
        'total_unis':               total_unis,
        'user_score':               (f"{profile.gpa} GPA" if profile.gpa else "—"),
        'matched_unis':             len(recommended),
        'essay_count':              Essay.objects.filter(user=request.user).count(),
    })


@login_required
def volunteer_view(request):
    profile, _  = AbituriyentProfile.objects.get_or_create(user=request.user)
    activities  = VolunteerActivity.objects.filter(user=request.user)
    total_hours = activities.aggregate(total=Sum('hours'))['total'] or 0
    if total_hours != profile.volunteer_hours:
        profile.volunteer_hours = total_hours
        profile.save(update_fields=['volunteer_hours'])
    return render(request, 'dashboard/volunteer.html', {
        'profile':     profile,
        'activities':  activities,
        'total_hours': total_hours,
        'count':       activities.count(),
    })


@login_required
def volunteer_add_view(request):
    if request.method == 'POST':
        org        = request.POST.get('organization', '').strip()
        role       = request.POST.get('role', '').strip()
        desc       = request.POST.get('description', '').strip()
        hours      = request.POST.get('hours', '0')
        start_date = request.POST.get('start_date', '')
        end_date   = request.POST.get('end_date', '') or None
        is_ongoing = 'is_ongoing' in request.POST

        if not org or not role or not start_date:
            return render(request, 'dashboard/volunteer_add.html', {
                'error': "Tashkilot, vazifa va boshlangan sana majburiy!",
                'post':  request.POST,
            })

        activity = VolunteerActivity.objects.create(
            user=request.user, organization=org, role=role,
            description=desc, hours=int(hours) if str(hours).isdigit() else 0,
            start_date=start_date, end_date=end_date, is_ongoing=is_ongoing,
        )
        if 'certificate' in request.FILES:
            activity.certificate = request.FILES['certificate']
            activity.save()
        _ai_generate_cv_text(activity)

        profile, _ = AbituriyentProfile.objects.get_or_create(user=request.user)
        total = VolunteerActivity.objects.filter(user=request.user).aggregate(total=Sum('hours'))['total'] or 0
        profile.volunteer_hours = total
        profile.save(update_fields=['volunteer_hours'])
        return redirect('dashboard:volunteer')

    return render(request, 'dashboard/volunteer_add.html')


@login_required
def volunteer_delete_view(request, pk):
    activity = get_object_or_404(VolunteerActivity, pk=pk, user=request.user)
    if request.method == 'POST':
        activity.delete()
        profile, _ = AbituriyentProfile.objects.get_or_create(user=request.user)
        total = VolunteerActivity.objects.filter(user=request.user).aggregate(total=Sum('hours'))['total'] or 0
        profile.volunteer_hours = total
        profile.save(update_fields=['volunteer_hours'])
    return redirect('dashboard:volunteer')


@login_required
def essays_view(request):
    profile, _ = AbituriyentProfile.objects.get_or_create(user=request.user)
    essays     = Essay.objects.filter(user=request.user)
    scored     = [e.ai_score for e in essays if e.ai_score is not None]
    avg_score  = round(sum(scored) / len(scored), 1) if scored else None
    return render(request, 'dashboard/essays.html', {
        'profile':   profile,
        'essays':    essays,
        'total':     essays.count(),
        'reviewed':  essays.filter(status='reviewed').count(),
        'avg_score': avg_score,
    })


@login_required
def essay_write_view(request):
    essay_id = request.GET.get('id')
    essay    = None
    if essay_id:
        essay = get_object_or_404(Essay, id=essay_id, user=request.user)

    if request.method == 'POST':
        title      = request.POST.get('title', '').strip()
        essay_type = request.POST.get('essay_type', 'motivation')
        content    = request.POST.get('content', '').strip()
        if not title or not content:
            return render(request, 'dashboard/essay_write.html', {
                'essay': essay,
                'error': "Sarlavha va matn bo'sh bo'lmasin.",
            })
        if essay:
            essay.title = title; essay.essay_type = essay_type
            essay.content = content; essay.status = 'draft'
            essay.save()
        else:
            essay = Essay.objects.create(
                user=request.user, title=title,
                essay_type=essay_type, content=content, status='draft',
            )
        _ai_review_essay(essay)
        return redirect('dashboard:essay_detail', pk=essay.pk)

    return render(request, 'dashboard/essay_write.html', {'essay': essay})


@login_required
def essay_detail_view(request, pk):
    essay = get_object_or_404(Essay, pk=pk, user=request.user)
    return render(request, 'dashboard/essay_detail.html', {'essay': essay})


@login_required
def essay_delete_view(request, pk):
    essay = get_object_or_404(Essay, pk=pk, user=request.user)
    if request.method == 'POST':
        essay.delete()
    return redirect('dashboard:essays')


@login_required
def leaderboard_view(request):
    top_users = AbituriyentProfile.objects.filter(
        profile_completed=True
    ).select_related('user').order_by('-gpa')[:20]
    return render(request, 'dashboard/leaderboard.html', {'top_users': top_users})


def _ai_review_essay(essay):
    from ai_engine.services import get_ai_response
    prompt = f"""Siz professional essay muharririsi siz.
Quyidagi "{essay.get_essay_type_display()}" essayini baholab, JSON formatda javob bering.

ESSAY MATNI:
{essay.content[:3000]}

FAQAT JSON FORMATDA:
{{
  "score": 78,
  "feedback": "Umumiy baho (2-3 gap)",
  "strengths": ["Kuchli tomon 1", "Kuchli tomon 2"],
  "weaknesses": ["Zaif tomon 1", "Zaif tomon 2"],
  "suggestions": ["Tavsiya 1", "Tavsiya 2", "Tavsiya 3"]
}}"""
    try:
        raw   = get_ai_response([{"role": "user", "content": prompt}])
        clean = raw.strip().lstrip('`').rstrip('`')
        if clean.startswith('json'): clean = clean[4:].strip()
        data  = json.loads(clean)
        essay.ai_score       = data.get('score', 0)
        essay.ai_feedback    = data.get('feedback', '')
        essay.ai_strengths   = json.dumps(data.get('strengths', []), ensure_ascii=False)
        essay.ai_weaknesses  = json.dumps(data.get('weaknesses', []), ensure_ascii=False)
        essay.ai_suggestions = json.dumps(data.get('suggestions', []), ensure_ascii=False)
        essay.status         = 'reviewed'
        essay.ai_reviewed_at = timezone.now()
        essay.save()
    except Exception as e:
        essay.ai_feedback = f"AI tahlil qila olmadi: {str(e)[:200]}"
        essay.status      = 'reviewed'
        essay.save()


def _ai_generate_cv_text(activity):
    from ai_engine.services import get_ai_response
    prompt = f"""Quyidagi volontyor faoliyatni CV uchun professional 2-3 qatorli inglizcha matn qiling:
Tashkilot: {activity.organization}
Vazifa: {activity.role}
Tavsif: {activity.description}
Davomiyligi: {activity.date_range}
Soat: {activity.hours} soat
Faqat CV matni yozing."""
    try:
        text = get_ai_response([{"role": "user", "content": prompt}])
        activity.ai_cv_text = text
        activity.save(update_fields=['ai_cv_text'])
    except Exception:
        pass