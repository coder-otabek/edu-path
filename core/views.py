"""core/views.py"""
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import SiteSettings


def manifest_view(request):
    site = SiteSettings.get()
    icons = []
    if site and site.favicon:
        icons = [{"src": site.favicon.url, "sizes": "192x192", "type": "image/png", "purpose": "any maskable"}]
    data = {
        "name":             site.name if site else "EduPath",
        "short_name":       site.short_name if site else "EduPath",
        "description":      site.meta_description if site else "",
        "start_url":        "/",
        "display":          "standalone",
        "background_color": "#F8FAFF",
        "theme_color":      "#2563EB",
        "orientation":      "portrait-primary",
        "categories":       ["education"],
        "lang":             "uz",
        "icons":            icons,
    }
    return JsonResponse(data)


def landing_view(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    return render(request, 'accounts/onboarding_landing.html')


def terms_view(request):
    return render(request, 'core/terms.html')


def privacy_view(request):
    return render(request, 'core/privacy.html')


def handler_404(request, exception=None):
    return render(request, '404.html', status=404)


def handler_500(request):
    return render(request, '500.html', status=500)


from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json as _json


@login_required
def videos_view(request):
    from .models import VideoLesson, VideoProgress

    videos = list(VideoLesson.objects.filter(is_active=True))
    progress_map = {p.video_id: p for p in VideoProgress.objects.filter(user=request.user)}

    # Barcha videolar ochiq
    unlocked_ids = {v.id for v in videos}

    # Template uchun (video, prog) tuple list
    video_list = [(v, progress_map.get(v.id)) for v in videos]

    return render(request, 'core/videos.html', {
        'video_list':   video_list,
        'unlocked_ids': unlocked_ids,
    })


@login_required
def video_detail_view(request, pk):
    from .models import VideoLesson, VideoProgress
    from django.shortcuts import get_object_or_404

    video  = get_object_or_404(VideoLesson, pk=pk, is_active=True)
    videos = list(VideoLesson.objects.filter(is_active=True))
    progress_map = {p.video_id: p for p in VideoProgress.objects.filter(user=request.user)}

    # Barcha videolar ochiq — tekshiruv yo'q

    my_progress = progress_map.get(video.id)

    idx = next((i for i, v in enumerate(videos) if v.id == video.id), None)
    next_video = videos[idx + 1] if idx is not None and idx + 1 < len(videos) else None

    return render(request, 'core/video_detail.html', {
        'video':       video,
        'my_progress': my_progress,
        'next_video':  next_video,
    })


@login_required
@require_POST
def video_progress_view(request):
    from .models import VideoLesson, VideoProgress
    try:
        data     = _json.loads(request.body)
        video_id = data.get('video_id')
        position = float(data.get('position', 0))
        watched  = bool(data.get('watched', False))

        video  = VideoLesson.objects.get(pk=video_id, is_active=True)
        obj, _ = VideoProgress.objects.get_or_create(user=request.user, video=video)
        obj.position = position
        if watched:
            obj.watched = True   # bir marta True bo'lsa qayta False bo'lmaydi
        obj.save()
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)