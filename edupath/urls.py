"""edupath/urls.py"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = []

# Media va static — ENG BIRINCHI (handler404 dan oldin)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += [
    path('admin/', admin.site.urls),

    path('accounts/',     include('accounts.urls',    namespace='accounts')),
    path('dashboard/',    include('dashboard.urls',    namespace='dashboard')),
    path('universities/', include('universities.urls', namespace='universities')),
    path('ai/',           include('ai_engine.urls',    namespace='ai_engine')),
    path('core/',         include('core.urls',         namespace='core')),

    path('manifest.json', core_views.manifest_view, name='manifest'),
    path('',              core_views.landing_view,  name='landing'),
]

handler404 = 'core.views.handler_404'
handler500 = 'core.views.handler_500'