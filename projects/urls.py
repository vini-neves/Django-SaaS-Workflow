from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from projects import views as project_views

urlpatterns = [
    # --- KANBAN UNIFICADO ---
    path('', views.dashboard, name='dashboard'), 
    path('kanban/', views.kanban_view, {'kanban_type': 'general'}, name='kanban_general'),
    path('kanban/operational/', views.kanban_view, {'kanban_type': 'operational'}, name='kanban_operational'),
    
    # --- GESTÃO DE CLIENTES ---
    path('clients/', views.client_list_create, name='client_list'),
    path('api/clients/add/', views.AddClientAPI.as_view(), name='add_client_api'),
    path('api/clients/<int:pk>/details/', views.client_detail_api, name='client_detail_api'),
    path('clients/<int:pk>/metrics/', views.client_metrics_dashboard, name='client_metrics'),
    path('api/clients/<int:pk>/get/', views.get_client_data_api, name='get_client_data_api'),
    path('api/clients/save/', views.AddClientAPI.as_view(), name='add_client_api'),
    path('api/clients/list-simple/', views.get_clients_list_api, name='get_clients_list_api'),

    # --- CALENDÁRIO ---
    path('calendar/', views.calendar_view, name='calendar_view'),
    path('api/calendar/events/', views.get_calendar_events, name='get_calendar_events'),
    path('api/calendar/add/', views.add_calendar_event, name='add_calendar_event'),
    path('api/calendar/clients/', views.get_clients_for_select, name='get_clients_for_select'),

    # --- POSTAGENS E SOCIAL MEDIA ---
    path('social/', views.social_dashboard, name='social_dashboard'),
    path('api/social/create-post/', views.CreateSocialPostAPI.as_view(), name='create_social_post_api'),
    
    # --- APIs DE TAREFAS ---
    path('api/task/update-status/', views.KanbanUpdateTask.as_view(), name='kanban_update_task'),
    path('api/task/add/', views.AddTaskAPI.as_view(), name='add_task_api'),
    path('api/task/<int:pk>/details/', views.get_task_details_api, name='get_task_details_api'),
    path('api/task/<int:pk>/delete/', views.DeleteTaskAPI.as_view(), name='delete_task_api'),

    #URL do Dashboard
    path('', views.dashboard, name='dashboard'),

    #Url de Projeto
    path('api/projects/add/', views.AddProjectAPI.as_view(), name='add_project_api'),
    
    # --- FLUXO DE LOGIN / LOGOUT ---
    path('login/', views.TenantLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='projects/logout.html'), name='logout'),

    # --- NOVO: FLUXO DE "ESQUECI A SENHA" ---
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='projects/password_reset_form.html', email_template_name='projects/password_reset_email.html', subject_template_name='projects/password_reset_subject.txt'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='projects/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='projects/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='projects/password_reset_complete.html'), name='password_reset_complete'),

    # Url de Redes sociais
# DASHBOARD SOCIAL
    path('social/', views.social_dashboard, name='social_dashboard'),
    
    # ESTÚDIO DE CRIAÇÃO (Tela Cheia)
    path('social/create/', views.create_post_studio_view, name='create_post_studio'),
    
    # API QUE SALVA O POST
    path('api/social/create-post/', views.CreateSocialPostAPI.as_view(), name='create_social_post_api'),
    path('api/social/send-approval/<int:post_id>/', views.send_approval_link, name='send_approval_link'),
    path('approval/<str:token>/', views.external_approval_view, name='external_approval_view'), 
    path('api/approval/action/', views.approval_action, name='approval_action'),

    # Kanban Unificado (Geral e Operacional)
    path('kanban/<str:kanban_type>/', views.kanban_view, name='kanban_view'),
    
    # API para Mover Cards (Drag & Drop)
    path('api/task/update-status/', views.KanbanUpdateTask.as_view(), name='kanban_update_task'),

    # APIs de Criação
    path('api/task/add-operational/', views.AddOperationalTaskAPI.as_view(), name='add_operational_task'),

    # --- FLUXO DE APROVAÇÃO EXTERNA ---
    # 1. Gerar link (Uso interno)
    path('api/social/generate-link/<int:post_id>/', views.send_approval_link, name='send_approval_link'),
    
    # 2. Tela do Cliente (Pública)
    path('approval/<str:token>/', views.external_approval_view, name='external_approval_view'),
    
    # 3. Ação do Cliente (Aprovar/Reprovar via API)
    path('api/approval/action/', views.ProcessApprovalAction.as_view(), name='process_approval_action'),
    path('social/create/', views.create_post_studio_view, name='create_post_studio'),

    # Rotas da Meta
    path('meta/connect/<int:client_id>/', project_views.meta_auth_start, name='meta_auth_start'),
    path('meta-callback/', project_views.meta_auth_callback, name='meta_auth_callback'),
]