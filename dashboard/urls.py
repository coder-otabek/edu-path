"""dashboard/urls.py"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('',                           views.home_view,            name='home'),
    path('volunteer/',                 views.volunteer_view,       name='volunteer'),
    path('volunteer/add/',             views.volunteer_add_view,   name='volunteer_add'),
    path('volunteer/<int:pk>/delete/', views.volunteer_delete_view,name='volunteer_delete'),
    path('essays/',                    views.essays_view,          name='essays'),
    path('essays/write/',              views.essay_write_view,     name='essay_write'),
    path('essays/<int:pk>/',           views.essay_detail_view,    name='essay_detail'),
    path('essays/<int:pk>/delete/',    views.essay_delete_view,    name='essay_delete'),
    path('leaderboard/',               views.leaderboard_view,     name='leaderboard'),
]