"""
ai_engine/services.py
AI provider bilan ishlash — admin paneldan dinamik boshqariladi.
Claude / OpenAI / Gemini / DeepSeek / Groq qo'llab-quvvatlanadi.
"""


def get_ai_response(messages: list, system_prompt: str = "") -> str:
    from core.models import AISettings
    config = AISettings.get()

    if not config:
        return "AI sozlamalari topilmadi. Admin panelda AISettings ni to'ldiring."

    if not config.api_key:
        return "AI API kalit kiritilmagan. Admin panel → AISettings → api_key."

    provider = config.provider

    try:
        if provider == 'claude':
            return _call_claude(config, messages, system_prompt)
        elif provider == 'openai':
            return _call_openai(config, messages, system_prompt)
        elif provider == 'gemini':
            return _call_gemini(config, messages, system_prompt)
        elif provider == 'deepseek':
            return _call_deepseek(config, messages, system_prompt)
        elif provider == 'groq':
            return _call_groq(config, messages, system_prompt)
        else:
            return f"Noma'lum AI provider: '{provider}'."
    except Exception as e:
        return f"AI xatosi ({provider}): {str(e)}"


def _call_claude(config, messages, system_prompt):
    import anthropic
    client = anthropic.Anthropic(api_key=config.api_key)
    kwargs = dict(
        model      = config.model_name or "claude-haiku-4-5-20251001",
        max_tokens = config.max_tokens or 2000,
        messages   = messages,
    )
    if system_prompt:
        kwargs['system'] = system_prompt
    response = client.messages.create(**kwargs)
    return response.content[0].text


def _call_openai(config, messages, system_prompt):
    from openai import OpenAI
    client = OpenAI(api_key=config.api_key)
    all_msgs = []
    if system_prompt:
        all_msgs.append({"role": "system", "content": system_prompt})
    all_msgs.extend(messages)
    response = client.chat.completions.create(
        model       = config.model_name or "gpt-4o-mini",
        messages    = all_msgs,
        max_tokens  = config.max_tokens or 2000,
        temperature = config.temperature or 0.7,
    )
    return response.choices[0].message.content


def _call_gemini(config, messages, system_prompt):
    import google.generativeai as genai
    genai.configure(api_key=config.api_key)
    full_prompt = ""
    if system_prompt:
        full_prompt += system_prompt + "\n\n"
    for m in messages:
        role = "Foydalanuvchi" if m["role"] == "user" else "AI"
        full_prompt += f"{role}: {m['content']}\n"
    full_prompt += "AI:"
    model    = genai.GenerativeModel(config.model_name or "gemini-2.0-flash")
    response = model.generate_content(full_prompt)
    return response.text


def _call_deepseek(config, messages, system_prompt):
    from openai import OpenAI
    client = OpenAI(api_key=config.api_key, base_url="https://api.deepseek.com")
    all_msgs = []
    if system_prompt:
        all_msgs.append({"role": "system", "content": system_prompt})
    all_msgs.extend(messages)
    response = client.chat.completions.create(
        model      = config.model_name or "deepseek-chat",
        messages   = all_msgs,
        max_tokens = config.max_tokens or 2000,
    )
    return response.choices[0].message.content


def _call_groq(config, messages, system_prompt):
    from openai import OpenAI
    client = OpenAI(
        api_key  = config.api_key,
        base_url = "https://api.groq.com/openai/v1"
    )
    all_msgs = []
    if system_prompt:
        all_msgs.append({"role": "system", "content": system_prompt})
    all_msgs.extend(messages)
    response = client.chat.completions.create(
        model       = config.model_name or "llama-3.3-70b-versatile",
        messages    = all_msgs,
        max_tokens  = config.max_tokens or 2000,
        temperature = config.temperature or 0.7,
    )
    return response.choices[0].message.content


def build_roadmap_prompt(profile) -> str:
    lang_skills = ""
    if profile.language_skills:
        try:
            skills = profile.language_skills
            if isinstance(skills, list):
                lang_skills = ", ".join(
                    f"{s.get('lang','').upper()} {s.get('level','')}"
                    for s in skills if isinstance(s, dict)
                )
        except Exception:
            pass

    # Foydalanuvchi tili
    user_lang = getattr(profile.user, 'language', 'uz') or 'uz'
    lang_map = {
        'uz': ("o'zbek", "o'zbek tilida"),
        'ru': ("русский", "на русском языке"),
        'en': ("english", "in English"),
    }
    lang_name, lang_instruction = lang_map.get(user_lang, lang_map['uz'])

    return f"""You are EduPath AI advisor. Create a detailed road map for this student.
IMPORTANT: Write ALL text values (summary, step titles, descriptions, tips) {lang_instruction}.

STUDENT PROFILE:
- Name: {profile.user.get_full_name()}
- IELTS: {profile.ielts_score or 'not provided'}
- SAT: {profile.sat_score or 'not provided'}
- GPA: {profile.gpa or 'not provided'}
- Olympiad: {profile.olympiad_level or 'none'}
- Main subject: {profile.get_main_subject_display() if profile.main_subject else 'not provided'}
- Direction: {profile.desired_specialty or 'not provided'}
- Degree: {profile.get_desired_degree_display()}
- Study type: {profile.get_study_type_display()}
- Needs grant: {'Yes' if profile.needs_grant else 'No'}
- Volunteer hours: {profile.volunteer_hours}
- Work experience: {'Yes' if profile.has_work_experience else 'No'}

RESPOND ONLY IN THIS JSON FORMAT (no other text):
{{
  "summary": "Overall assessment 2-3 sentences ({lang_instruction})",
  "strength_score": 75,
  "steps": [
    {{
      "id": 1,
      "title": "Step title ({lang_instruction})",
      "description": "What to do (specific, {lang_instruction})",
      "deadline": "2025-09",
      "status": "active",
      "priority": "high"
    }}
  ],
  "recommended_universities": ["Uni 1", "Uni 2", "Uni 3"],
  "tips": ["Tip 1 ({lang_instruction})", "Tip 2", "Tip 3"]
}}

status: "active" | "pending" | "done"
priority: "high" | "medium" | "low"
Write at least 5 steps and 3 tips.""".strip()