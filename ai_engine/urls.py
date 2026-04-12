"""ai_engine/urls.py"""
from django.urls import path
from . import views

app_name = 'ai_engine'

urlpatterns = [
    path('roadmap/',   views.roadmap_view,    name='roadmap'),
    path('chat/',      views.chat_view,       name='chat'),
    path('chat/send/', views.chat_send_view,  name='chat_send'),
]
