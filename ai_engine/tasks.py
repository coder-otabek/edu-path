"""
ai_engine/tasks.py
Celery background tasks.
Celery ishlamasa ham sync ishlashi uchun fallback mavjud.
"""
import json

try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    def shared_task(fn):
        """Celery yo'q bo'lganda decorator simulyatsiyasi"""
        fn.delay = fn
        return fn


@shared_task
def process_university_content(content_id: int):
    """Universitet content faylini AI bilan tahlil qilish"""
    from universities.models import UniversityContent
    from .services import get_ai_response

    try:
        obj  = UniversityContent.objects.get(id=content_id)
        text = _extract_text(obj)
        if not text.strip():
            return f"content_id={content_id}: matn topilmadi"

        prompt  = f"Quyidagi universitet ma'lumotini o'qib, eng muhim faktlarni ajrat:\n\n{text[:4000]}"
        summary = get_ai_response([{"role": "user", "content": prompt}])

        obj.ai_extracted = text[:5000]
        obj.ai_summary   = summary
        obj.ai_processed = True
        obj.save(update_fields=['ai_extracted', 'ai_summary', 'ai_processed'])

        _update_university_summary(obj.university)
        return f"OK: content_id={content_id}"

    except UniversityContent.DoesNotExist:
        return f"ERROR: content_id={content_id} topilmadi"
    except Exception as e:
        return f"ERROR: {e}"


def _extract_text(obj) -> str:
    """Fayl turiga qarab matn chiqarish"""
    if obj.text_content:
        return obj.text_content

    if not obj.file:
        return ""

    file_path = obj.file.path
    ct        = obj.content_type

    try:
        if ct == 'pdf':
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                return "\n".join(p.extract_text() or "" for p in reader.pages)

        elif ct == 'docx':
            from docx import Document
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)

        elif ct == 'image':
            try:
                import pytesseract
                from PIL import Image
                return pytesseract.image_to_string(Image.open(file_path), lang='uzb+eng+rus')
            except Exception:
                return ""

        elif ct in ('audio', 'video'):
            try:
                import whisper
                model  = whisper.load_model("base")
                result = model.transcribe(file_path)
                return result.get("text", "")
            except Exception:
                return ""

    except Exception as e:
        print(f"[EduPath] Text extract error ({ct}): {e}")

    return ""


def _update_university_summary(university):
    """Universitettning umumiy AI xulosasini yangilash"""
    from .services import get_ai_response
    summaries = university.contents.filter(
        ai_processed=True
    ).values_list('ai_summary', flat=True)
    combined = "\n\n".join(s for s in summaries if s)[:5000]
    if combined:
        prompt  = f"{university.name} universiteti haqida qisqa xulosa yoz (3-5 gap):\n\n{combined}"
        summary = get_ai_response([{"role": "user", "content": prompt}])
        university.ai_summary = summary
        university.save(update_fields=['ai_summary'])


@shared_task
def generate_roadmap(user_id: int):
    """Foydalanuvchi uchun AI road map generatsiya qilish"""
    from accounts.models import AbituriyentProfile
    from .models import RoadMap
    from .services import get_ai_response, build_roadmap_prompt
    from core.models import AISettings

    try:
        profile = AbituriyentProfile.objects.select_related('user').get(user_id=user_id)
        prompt  = build_roadmap_prompt(profile)
        raw     = get_ai_response([{"role": "user", "content": prompt}])

        # JSON parse — backtick va whitespace tozalash
        clean = raw.strip()
        clean = clean.lstrip('`').rstrip('`')
        if clean.startswith('json'):
            clean = clean[4:]
        clean = clean.strip()

        try:
            data = json.loads(clean)
        except json.JSONDecodeError:
            # JSON topilmasa — minimal struktura yaratamiz
            data = {
                "summary":   raw[:300],
                "strength_score": 50,
                "steps": [
                    {"id": 1, "title": "Profilni to'ldiring", "description": "Barcha akademik ma'lumotlarni kiriting",
                     "deadline": "", "status": "active", "priority": "high"}
                ],
                "recommended_universities": [],
                "tips": [raw[:200]] if raw else []
            }

        config = AISettings.get()
        RoadMap.objects.update_or_create(
            user_id=user_id,
            defaults={
                'content':     data,
                'ai_provider': config.provider if config else '',
            }
        )
        return f"OK: roadmap generated for user_id={user_id}"

    except AbituriyentProfile.DoesNotExist:
        return f"ERROR: profile topilmadi user_id={user_id}"
    except Exception as e:
        return f"ERROR: {e}"
