"""universities/urls.py"""
from django.urls import path
from . import views

app_name = 'universities'

urlpatterns = [
    # Universitetlar ro'yxati
    path('',                                          views.university_list,         name='list'),

    # Mustaqil grantlar — 'grants' URL ham shu yerga
    path('grants/',                                   views.standalone_grant_list,   name='grants'),
    path('standalone/',                               views.standalone_grant_list,   name='standalone_list'),
    path('standalone/<slug:slug>/',                   views.standalone_grant_detail, name='standalone_grant_detail'),

    # Universitet detail + grantlar
    path('<slug:slug>/',                              views.university_detail,       name='detail'),
    path('<slug:uni_slug>/grants/<int:grant_id>/',    views.grant_detail,            name='grant_detail'),

    # Esse tekshirish
    path('essay/check/',                              views.essay_check_view,        name='essay_check'),
    path('essay/check/api/',                          views.essay_check_api,         name='essay_check_api'),
]