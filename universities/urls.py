"""universities/urls.py"""
from django.urls import path
from . import views

app_name = 'universities'

urlpatterns = [
    path('',                                                          views.university_list,           name='list'),
    path('grants/',                                                   views.standalone_grant_list,     name='grants'),
    path('standalone/',                                               views.standalone_grant_list,     name='standalone_list'),
    path('standalone/<slug:slug>/',                                   views.standalone_grant_detail,   name='standalone_grant_detail'),

    # Video detail sahifasi
    path('standalone/<slug:grant_slug>/video/<int:video_id>/',        views.standalone_video_detail,   name='standalone_video_detail'),

    # Video testi
    path('standalone/<slug:grant_slug>/video/<int:video_id>/test/',          views.video_test_view,   name='video_test'),
    path('standalone/<slug:grant_slug>/video/<int:video_id>/test/submit/',   views.video_test_submit, name='video_test_submit'),

    path('<slug:slug>/',                                              views.university_detail,         name='detail'),
    path('<slug:uni_slug>/grants/<int:grant_id>/',                    views.grant_detail,              name='grant_detail'),
    path('essay/check/',                                              views.essay_check_view,          name='essay_check'),
    path('essay/check/api/',                                          views.essay_check_api,           name='essay_check_api'),
]