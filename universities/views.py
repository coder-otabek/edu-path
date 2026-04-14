"""universities/views.py"""
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q

from .models import University, Grant, GrantVideo, EssaySample, GRANT_TYPE_CHOICES


# ─── Universitetlar ro'yxati ─────────────────────────────────
@login_required
def university_list(request):
    """Xorijiy / Mahalliy filtr bilan universitetlar ro'yxati"""
    grant_type = request.GET.get('type', '')   # 'foreign' | 'local' | ''
    search     = request.GET.get('q', '').strip()
    country    = request.GET.get('country', '')
    degree     = request.GET.get('degree', '')

    unis = University.objects.filter(is_published=True).prefetch_related('specialties', 'grants')

    if grant_type in ('foreign', 'local'):
        # 'both' turdagi universitetlar ham foreign va local filtrlarda chiqishi kerak
        unis = unis.filter(Q(grant_type=grant_type) | Q(grant_type='both'))
    if search:
        unis = unis.filter(
            Q(name__icontains=search) |
            Q(city__icontains=search) |
            Q(description__icontains=search)
        )
    if country:
        unis = unis.filter(country=country)

    # Grant soni bilan
    from django.db.models import Count
    unis = unis.annotate(grant_count=Count('grants', filter=Q(grants__is_active=True)))

    # Har xil mamlakatlar ro'yxati
    all_countries = University.objects.filter(is_published=True).values_list(
        'country', flat=True
    ).distinct()

    return render(request, 'universities/university_list.html', {
        'universities':   unis,
        'grant_type':     grant_type,
        'search':         search,
        'country':        country,
        'all_countries':  all_countries,
        'grant_type_choices': GRANT_TYPE_CHOICES,
    })


# ─── Universitet detail ──────────────────────────────────────
@login_required
def university_detail(request, slug):
    """Universitetning barcha grantlari"""
    uni = get_object_or_404(University, slug=slug, is_published=True)

    grant_type = request.GET.get('type', '')
    grants     = uni.grants.filter(is_active=True).prefetch_related('videos')

    if grant_type in ('foreign', 'local'):
        grants = grants.filter(Q(grant_type=grant_type) | Q(grant_type='both'))

    return render(request, 'universities/university_detail.html', {
        'university':    uni,
        'grants':        grants,
        'grant_type':    grant_type,
        'foreign_count': uni.grants.filter(is_active=True).filter(Q(grant_type='foreign') | Q(grant_type='both')).count(),
        'local_count':   uni.grants.filter(is_active=True).filter(Q(grant_type='local') | Q(grant_type='both')).count(),
    })


# ─── Grant detail ────────────────────────────────────────────
@login_required
def grant_detail(request, uni_slug, grant_id):
    """Grant ma'lumotlari + video qo'llanmalar"""
    uni   = get_object_or_404(University, slug=uni_slug, is_published=True)
    grant = get_object_or_404(Grant, pk=grant_id, university=uni)
    videos = grant.videos.filter(is_published=True).order_by('order')

    return render(request, 'universities/grant_detail.html', {
        'university': uni,
        'grant':      grant,
        'videos':     videos,
    })


# ─── Essay tekshirish ────────────────────────────────────────
@login_required
def essay_check_view(request):
    """User esseni yuboradi → AI namuna esseylar asosida tekshiradi"""
    return render(request, 'universities/essay_check.html', {
        'essay_types': EssaySample._meta.get_field('essay_type').choices,
    })


@login_required
@require_POST
def essay_check_api(request):
    """AJAX: essay matni + turi → AI tekshiradi"""
    try:
        data       = json.loads(request.body)
        essay_text = data.get('essay', '').strip()
        essay_type = data.get('essay_type', 'general')
        language   = data.get('language', 'en')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': "Noto'g'ri so'rov"}, status=400)

    if not essay_text:
        return JsonResponse({'error': "Esse bo'sh"}, status=400)

    if len(essay_text.split()) < 30:
        return JsonResponse({'error': "Esse juda qisqa (kamida 30 so'z bo'lishi kerak)"}, status=400)

    # Namuna esseylarni olish (faqat mos tur + faol)
    samples = EssaySample.objects.filter(is_active=True)
    type_samples = samples.filter(essay_type=essay_type)
    if not type_samples.exists():
        type_samples = samples.filter(essay_type='general')

    # Eng yaxshi 3 ta namuna
    sample_texts = ""
    for i, s in enumerate(type_samples.order_by('-score')[:3], 1):
        sample_texts += f"""
--- NAMUNA ESSE #{i} ({s.get_essay_type_display()}, {s.score}⭐) ---
{s.content[:800]}
{"Struktura izohi: " + s.structure_notes if s.structure_notes else ""}
"""

    if not sample_texts:
        sample_texts = "Namuna esseylar hali kiritilmagan."

    # Til
    lang_map = {
        'en': ('ingliz', 'Respond in English'),
        'uz': ("o'zbek", "O'zbek tilida javob bering"),
        'ru': ('rus', 'Отвечайте на русском языке'),
    }
    lang_name, lang_instruction = lang_map.get(language, lang_map['en'])

    # AI prompt
    system = f"""Siz tajribali universitet esse maslahatchisisiz.
Sizda yuqori sifatli namuna esseylar mavjud. Ularning strukturasi va uslubiga asoslanib, user essesini REAL va ANIQ tekshirasiz.

NAMUNA ESSEYLAR:
{sample_texts}

BAHOLASH MEZONLARI:
1. Hook (kirish) — diqqatni tortadimi?
2. Storytelling — shaxsiy voqea/tajriba bormi?
3. Specificity — aniq dalillar, raqamlar, misollarmi?
4. Structure — mantiqiy tuzilma (kirish → asosiy qism → xulosa)?
5. Tone — rasmiy, lekin shaxsiy ovoz?
6. Language — grammatika va uslub?
7. Word count — hajm maqsadga mosmi?

{lang_instruction}.

Javobni FAQAT quyidagi JSON formatda bering (hech qanday boshqa matn yo'q):
{{
  "overall_score": 72,
  "grade": "B+",
  "word_count": 350,
  "criteria": {{
    "hook":          {{"score": 80, "comment": "..."}},
    "storytelling":  {{"score": 65, "comment": "..."}},
    "specificity":   {{"score": 70, "comment": "..."}},
    "structure":     {{"score": 75, "comment": "..."}},
    "tone":          {{"score": 80, "comment": "..."}},
    "language":      {{"score": 70, "comment": "..."}}
  }},
  "strengths":     ["...", "..."],
  "improvements":  ["...", "..."],
  "rewrite_tip":   "Eng muhim 1-2 jumla: nima o'zgartirish kerak?",
  "revised_intro": "Kirish qismini qayta yozing (2-3 gap namuna)"
}}"""

    messages = [{"role": "user", "content": f"Mening essem ({essay_type}):\n\n{essay_text}"}]

    try:
        from ai_engine.services import get_ai_response
        raw = get_ai_response(messages, system_prompt=system)

        # JSON parse
        clean = raw.strip().lstrip('`').rstrip('`')
        if clean.startswith('json'):
            clean = clean[4:].strip()

        result = json.loads(clean)
        result['essay_type_display'] = dict(
            EssaySample._meta.get_field('essay_type').choices
        ).get(essay_type, essay_type)
        return JsonResponse({'ok': True, 'result': result})

    except json.JSONDecodeError:
        # JSON kelmasa — xom matn
        return JsonResponse({'ok': True, 'result': {'raw': raw, 'parse_error': True}})
    except Exception as e:
        return JsonResponse({'error': f"AI xatosi: {str(e)[:150]}"}, status=500)


# ─── Mustaqil Grantlar ro'yxati ──────────────────────────────
@login_required
def standalone_grant_list(request):
    """Universitetga bog'liq bo'lmagan mustaqil grantlar"""
    grant_type = request.GET.get('type', '')
    search     = request.GET.get('q', '').strip()

    from .models import StandaloneGrant
    grants = StandaloneGrant.objects.filter(is_active=True)

    if grant_type in ('foreign', 'local'):
        grants = grants.filter(Q(grant_type=grant_type) | Q(grant_type='both'))
    if search:
        grants = grants.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(directions__icontains=search)
        )

    return render(request, 'universities/standalone_grant_list.html', {
        'grants':     grants,
        'grant_type': grant_type,
        'search':     search,
    })


# ─── Mustaqil Grant detail ───────────────────────────────────
@login_required
def standalone_grant_detail(request, slug):
    from .models import StandaloneGrant
    grant  = get_object_or_404(StandaloneGrant, slug=slug, is_active=True)
    videos = grant.videos.filter(is_published=True).order_by('order')

    return render(request, 'universities/standalone_grant_detail.html', {
        'grant':  grant,
        'videos': videos,
    })


# ─── Grant Test ──────────────────────────────────────────────
@login_required

# ─── Video detail sahifasi ───────────────────────────────────
@login_required
def standalone_video_detail(request, grant_slug, video_id):
    """Video alohida sahifada ko'rish + test"""
    from .models import StandaloneGrant, StandaloneGrantVideo, GrantTest, GrantTestResult
    grant  = get_object_or_404(StandaloneGrant, slug=grant_slug, is_active=True)
    video  = get_object_or_404(StandaloneGrantVideo, pk=video_id, grant=grant, is_published=True)
    videos = grant.videos.filter(is_published=True).order_by('order')

    # Oldingi va keyingi video
    video_list = list(videos)
    current_idx = next((i for i, v in enumerate(video_list) if v.pk == video.pk), 0)
    prev_video  = video_list[current_idx - 1] if current_idx > 0 else None
    next_video  = video_list[current_idx + 1] if current_idx < len(video_list) - 1 else None

    # Test bormi
    try:
        test = video.test
        has_test = test.is_active and test.questions.exists()
    except GrantTest.DoesNotExist:
        test = None
        has_test = False

    # Test natijasi
    last_result = None
    if test:
        last_result = GrantTestResult.objects.filter(
            user=request.user, test=test
        ).order_by('-created_at').first()

    return render(request, 'universities/standalone_video_detail.html', {
        'grant':       grant,
        'video':       video,
        'videos':      videos,
        'prev_video':  prev_video,
        'next_video':  next_video,
        'test':        test,
        'has_test':    has_test,
        'last_result': last_result,
        'current_num': current_idx + 1,
        'total_num':   len(video_list),
    })


# ─── Video testi ─────────────────────────────────────────────
@login_required
def video_test_view(request, grant_slug, video_id):
    """Video testini ko'rsatish"""
    from .models import StandaloneGrant, StandaloneGrantVideo, GrantTest, GrantTestResult
    grant  = get_object_or_404(StandaloneGrant, slug=grant_slug, is_active=True)
    video  = get_object_or_404(StandaloneGrantVideo, pk=video_id, grant=grant, is_published=True)

    try:
        test = video.test
        if not test.is_active:
            return redirect('universities:standalone_video_detail',
                            grant_slug=grant_slug, video_id=video_id)
    except GrantTest.DoesNotExist:
        return redirect('universities:standalone_video_detail',
                        grant_slug=grant_slug, video_id=video_id)

    questions = test.questions.prefetch_related('choices').order_by('order')
    history   = GrantTestResult.objects.filter(
        user=request.user, test=test
    ).order_by('-created_at')[:5]

    return render(request, 'universities/grant_test.html', {
        'grant':     grant,
        'video':     video,
        'test':      test,
        'questions': questions,
        'history':   history,
        'submit_url': request.build_absolute_uri(
            f'/universities/standalone/{grant_slug}/video/{video_id}/test/submit/'
        ),
    })


@login_required
@require_POST
def video_test_submit(request, grant_slug, video_id):
    """Video test javoblarini qabul qilish"""
    import json as _json
    from .models import StandaloneGrant, StandaloneGrantVideo, GrantTest, GrantTestResult
    grant  = get_object_or_404(StandaloneGrant, slug=grant_slug, is_active=True)
    video  = get_object_or_404(StandaloneGrantVideo, pk=video_id, grant=grant)

    try:
        test = video.test
    except GrantTest.DoesNotExist:
        return JsonResponse({'error': 'Test topilmadi'}, status=404)

    try:
        data       = _json.loads(request.body)
        answers    = data.get('answers', {})
        time_spent = int(data.get('time_spent', 0))
    except Exception:
        return JsonResponse({'error': "Noto'g'ri so'rov"}, status=400)

    questions = test.questions.prefetch_related('choices')
    score     = 0
    total     = questions.count()
    details   = {}

    for q in questions:
        chosen_id  = answers.get(str(q.id))
        correct    = q.choices.filter(is_correct=True).first()
        is_correct = correct and str(correct.id) == str(chosen_id)
        if is_correct:
            score += 1
        details[str(q.id)] = {
            'chosen':      chosen_id,
            'correct':     str(correct.id) if correct else None,
            'is_correct':  is_correct,
            'explanation': q.explanation,
        }

    result = GrantTestResult.objects.create(
        user=request.user, test=test,
        score=score, total=total,
        time_spent=time_spent,
        answers=details,
    )

    return JsonResponse({
        'ok':        True,
        'score':     score,
        'total':     total,
        'percent':   result.percent,
        'passed':    result.is_passed,
        'grade':     result.grade,
        'time':      result.time_spent_display,
        'result_id': result.id,
        'details':   details,
    })