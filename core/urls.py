"""core/urls.py — faqat agar to'g'ridan-to'g'ri include qilinsa"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('videos/',              views.videos_view,         name='videos'),
    path('videos/progress/',     views.video_progress_view, name='video_progress'),
    path('videos/<int:pk>/',     views.video_detail_view,   name='video_detail'),
    path('terms/',   views.terms_view,   name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
]