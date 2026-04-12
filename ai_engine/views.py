"""ai_engine/views.py"""
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import RoadMap, ChatSession, ChatMessage
from .services import get_ai_response
from accounts.models import AbituriyentProfile

QUICK_SUGGESTIONS = {
    'uz': [
        "💡 Menga mos universitetlarni tavsiya qil",
        "📚 IELTS ballimni oshirish uchun yo'l xarita tuzib ber",
        "💰 Grant olish uchun qanday hujjatlar kerak?",
        "🗺️ Mening profilimga qarab road map tuzib ber",
        "🎓 Xorijda o'qish uchun qanday tayyorgarlik ko'rishim kerak?",
    ],
    'ru': [
        "💡 Подбери мне подходящие университеты",
        "📚 Составь план для повышения балла IELTS",
        "💰 Какие документы нужны для получения гранта?",
        "🗺️ Составь дорожную карту на основе моего профиля",
        "🎓 Как подготовиться к учёбе за рубежом?",
    ],
    'en': [
        "💡 Recommend universities that match my profile",
        "📚 Create a study plan to improve my IELTS score",
        "💰 What documents do I need for a grant?",
        "🗺️ Build a road map based on my profile",
        "🎓 How should I prepare to study abroad?",
    ],
}


@login_required
def roadmap_view(request):
    roadmap    = RoadMap.objects.filter(user=request.user).first()
    profile, _ = AbituriyentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        from .tasks import generate_roadmap
        from django.contrib import messages
        try:
            generate_roadmap.delay(request.user.id)
            messages.success(request, "Road map generatsiya boshlanmoqda. Sahifani yangilang.")
        except Exception:
            generate_roadmap(request.user.id)
            messages.success(request, "Road map muvaffaqiyatli yaratildi!")
        return redirect('ai_engine:roadmap')

    return render(request, 'ai_engine/roadmap.html', {
        'roadmap': roadmap,
        'profile': profile,
    })


@login_required
def chat_view(request):
    session_id  = request.GET.get('session')
    sessions    = ChatSession.objects.filter(user=request.user)[:20]
    session     = None
    messages_qs = []

    if session_id:
        try:
            session     = sessions.get(id=session_id)
            messages_qs = session.messages.all()
        except ChatSession.DoesNotExist:
            pass

    uni_query = request.GET.get('q', '')
    user_lang = getattr(request.user, 'language', 'uz') or 'uz'

    # Prefill matni foydalanuvchi tiliga qarab
    prefill_templates = {
        'uz': f"{uni_query} haqida menga ma'lumot bering",
        'ru': f"Расскажите мне о {uni_query}",
        'en': f"Tell me about {uni_query}",
    }
    prefill = prefill_templates.get(user_lang, prefill_templates['uz']) if uni_query else ''

    return render(request, 'ai_engine/chat.html', {
        'sessions':          sessions,
        'session':           session,
        'chat_messages':     messages_qs,
        'quick_suggestions': QUICK_SUGGESTIONS.get(user_lang, QUICK_SUGGESTIONS['uz']),
        'prefill':           prefill,
    })


@login_required
@require_POST
def chat_send_view(request):
    try:
        data       = json.loads(request.body)
        user_msg   = data.get('message', '').strip()
        session_id = data.get('session_id')
        user_lang  = data.get('lang', 'uz')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': "Noto'g'ri so'rov"}, status=400)

    if not user_msg:
        return JsonResponse({'error': "Xabar bo'sh"}, status=400)

    # Session
    if session_id:
        session, _ = ChatSession.objects.get_or_create(
            id=session_id, user=request.user,
            defaults={'title': user_msg[:50]}
        )
    else:
        session = ChatSession.objects.create(
            user=request.user, title=user_msg[:50]
        )

    ChatMessage.objects.create(session=session, role='user', content=user_msg)

    history     = list(session.messages.order_by('-created_at')[:20])[::-1]
    ai_messages = [{"role": m.role, "content": m.content} for m in history]

    # Til
    lang_names = {'uz': "o'zbek", 'ru': 'rus', 'en': 'ingliz'}
    lang_name  = lang_names.get(user_lang, "o'zbek")

    # Profil
    try:
        profile = AbituriyentProfile.objects.get(user=request.user)
        profile_text = f"""FOYDALANUVCHI PROFILI:
- Ism: {request.user.get_full_name()}
- IELTS: {profile.ielts_score or 'kiritilmagan'}
- SAT: {profile.sat_score or 'kiritilmagan'}
- GPA: {profile.gpa or 'kiritilmagan'}
- Yo'nalish: {profile.desired_specialty or 'kiritilmagan'}
- O'qish turi: {profile.get_study_type_display()}
- Grant kerakmi: {'Ha' if profile.needs_grant else "Yo'q"}
- Olimpiada: {profile.olympiad_level or "yo'q"}
- Volontyor soat: {profile.volunteer_hours or 0}
- Profil to'ldirilganlik: {profile.completion_percent}%"""
    except Exception:
        profile_text = f"Ism: {request.user.get_full_name()}"

    # Universitetlar bazasi
    try:
        from universities.models import University
        unis      = University.objects.filter(is_published=True).prefetch_related('specialties')
        unis_text = "\n\nUNIVERSITETLAR BAZASI:\n"
        if unis.exists():
            for uni in unis[:30]:
                specs = ", ".join(uni.specialties.values_list('name', flat=True)[:5])
                unis_text += f"""
- {uni.name} ({uni.city}, {uni.country})
  Grant: {"bor" if uni.has_grant else "yo'q"}
  Min IELTS: {uni.min_ielts_score or "noma'lum"}
  Tolov: {uni.tuition_fee_min or "?"}/yil
  Yonalishlar: {specs or "noma'lum"}"""
        else:
            unis_text += "Universitetlar kiritilmagan."
    except Exception as e:
        unis_text = f"\n(Universitetlar bazasini yuklashda xato: {e})"

    # Mustaqil grantlar bazasi
    try:
        from universities.models import StandaloneGrant
        sgrants = StandaloneGrant.objects.filter(is_active=True)
        if sgrants.exists():
            grants_text = "\n\nGRANTLAR BAZASI:\n"
            for g in sgrants[:50]:
                grants_text += f"""
- {g.name} ({g.get_grant_type_display()}, {g.get_country_display()})
  Daraja: {g.get_degree_display()}
  Mukofot: {g.amount or "noma'lum"}
  Muddat: {g.deadline_text or "noma'lum"}
  Kvota: {g.winners_count or "noma'lum"}
  Talablar: {g.requirements[:200] if g.requirements else "ko'rsatilmagan"}
  Yo'nalishlar: {g.directions[:150] if g.directions else "ko'rsatilmagan"}"""
            if sgrants.filter(universities__isnull=False).exists():
                grants_text += "\n(Ba'zi grantlar universitetlarga ham bog'langan)"
        else:
            grants_text = "\n\nGRANTLAR BAZASI: Hozircha grantlar kiritilmagan."
    except Exception as e:
        grants_text = f"\n(Grantlar bazasini yuklashda xato: {e})"

    # Web search
    def search_university_info(uni_name):
        try:
            import urllib.request, urllib.parse, json as _json
            query = urllib.parse.quote(f"{uni_name} university official admissions requirements")
            url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as r:
                data = _json.loads(r.read())
            abstract = data.get('AbstractText', '') or data.get('Answer', '')
            return abstract[:500] if abstract else ''
        except Exception:
            return ''

    web_info = ""
    try:
        from universities.models import University as _Uni
        for _uni in _Uni.objects.filter(is_published=True)[:5]:
            _info = search_university_info(_uni.name)
            if _info:
                web_info += f"\n[{_uni.name} - internet ma'lumoti]: {_info}"
    except Exception:
        pass

    system = f"""Siz EduPath platformasining AI maslahatchi siz.

QATTIQ QOIDALAR:
1. FAQAT ta'lim mavzularida javob bering: universitetlar, grantlar, stipendiyalar, qabul jarayoni, IELTS/SAT/TOEFL, essay, CV, xorijda o'qish.
2. Grantlar haqida so'ralganda — AVVAL bizning GRANTLAR BAZASIDAN qidiring va u yerdan javob bering.
3. Universitetlar haqida so'ralganda — AVVAL UNIVERSITETLAR BAZASIDAN qidiring.
4. Bazada topilsa — aniq ma'lumot bering. Topilmasa — umumiy bilimdan foydalaning va "⚠️ Bu ma'lumot umumiy manbadan, rasmiy sayt orqali tekshiring." deb ogohlantiring.
5. Hech qachon "admin paneldan qo'shilishi mumkin" dema — foydalanuvchiga bu kerak emas.
6. FAQAT {lang_name} tilida javob bering!

{profile_text}
{unis_text}
{grants_text}
{web_info if web_info else ''}

Qisqa, aniq va foydali javob bering."""

    try:
        ai_reply = get_ai_response(ai_messages, system_prompt=system)
    except Exception as e:
        ai_reply = f"Xatolik: {str(e)[:100]}. AI sozlamalarini tekshiring."

    ChatMessage.objects.create(session=session, role='assistant', content=ai_reply)

    return JsonResponse({'reply': ai_reply, 'session_id': session.id})