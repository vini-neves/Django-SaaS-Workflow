# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from projects import views as project_views

# 1. Importe as novas views do app 'accounts'
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # 2. Adicione as URLs de autenticação do Google AQUI
    path('google-auth-start/', accounts_views.google_auth_start, name='google_auth_start'),
    path('google-auth-callback/', accounts_views.google_auth_callback, name='google_auth_callback'),

    #URLs do Facebook
    path('meta/connect/<int:client_id>/', project_views.meta_auth_start, name='meta_auth_start'),
    path('meta-callback/', project_views.meta_auth_callback, name='meta_auth_callback'),

    #LinkedIn URLs
    path('linkedin/connect/<int:client_id>/', project_views.linkedin_auth_start, name='linkedin_auth_start'),
    path('linkedin-callback/', project_views.linkedin_auth_callback, name='linkedin_auth_callback'),
    
    #TikTok URLs
    path('tiktok/connect/<int:client_id>/', project_views.tiktok_auth_start, name='tiktok_auth_start'),
    path('tiktok-callback/', project_views.tiktok_auth_callback, name='tiktok_auth_callback'),
    
    path('', include('projects.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)