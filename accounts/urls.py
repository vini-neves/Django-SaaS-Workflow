# accounts/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('team/', views.user_management_view, name='user_list'),
    path('api/team/create/', views.create_user_api, name='create_user_api'),
]