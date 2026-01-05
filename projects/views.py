import json
import secrets
import datetime
import base64
import requests # Movido para o topo
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import models, connection
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import views as auth_views
from django.core.files.base import ContentFile

# Imports Locais
from .models import Task, CalendarEvent, Project, Client, SocialPost, SocialAccount, SocialPostDestination
from .forms import ClientForm, TenantAuthenticationForm, ProjectForm
from accounts.models import CustomUser
from .services import MetaService, LinkedInService, TikTokService

# ==============================================================================
# CONSTANTES GLOBAIS
# ==============================================================================

GENERAL_STAGES = [
    ('todo', 'A Fazer'),
    ('in_progress', 'Em Progresso'),
    ('done', 'Concluído'),
]

OPERATIONAL_STAGES = [
    ('briefing', 'Briefing'),
    ('copy', 'Copy'),
    ('design', 'Design'),
    ('internal_approval', 'Aprovação Interna'),
    ('client_approval', 'Aprovação Cliente'),
    ('scheduling', 'Agendamento da Postagem'),
]

# ==============================================================================
# 1. DASHBOARDS E VISÕES GERAIS
# ==============================================================================

class TenantLoginView(auth_views.LoginView):
    form_class = TenantAuthenticationForm
    template_name = 'projects/login.html'

@login_required
def dashboard(request):
    today = datetime.date.today()

    # Estatísticas
    project_count = Project.objects.count()
    pending_tasks_count = Task.objects.filter(status__in=['todo', 'in_progress']).count()
    completed_tasks_count = Task.objects.filter(status='done').count()
    total_tasks = pending_tasks_count + completed_tasks_count
    
    completion_percent = 0
    if total_tasks > 0:
        completion_percent = round((completed_tasks_count / total_tasks * 100))

    # Gráficos
    status_counts = Task.objects.values('status').annotate(count=models.Count('id'))
    chart_status_data = {item['status']: item['count'] for item in status_counts}

    posts_metrics = {
        'scheduled': SocialPost.objects.filter(scheduled_for__gte=timezone.now()).count(),
        'published': SocialPost.objects.filter(scheduled_for__lt=timezone.now()).count(),
        'pending_approval': Task.objects.filter(status='client_approval').count()
    }

    # Listas Recentes
    upcoming_events = CalendarEvent.objects.filter( date__gte=timezone.now().date()).order_by('date')[:5]
    recent_tasks = Task.objects.filter(status__in=['todo', 'in_progress']).order_by('-created_at')[:5]

    context = {
        'project_count': Project.objects.filter(status='active').count(),
        'pending_tasks_count': Task.objects.filter(status='pending').count(),
        'completed_tasks_count': completed_tasks_count,
        'total_tasks': total_tasks,
        'completion_percent': completion_percent,
        'upcoming_events': upcoming_events,
        'recent_tasks': recent_tasks,
        'chart_status_data': json.dumps(chart_status_data),
        'posts_metrics': json.dumps(posts_metrics),
    }
    return render(request, 'projects/dashboard.html', context)

@login_required
def social_dashboard(request):
    """Renderiza o painel principal com métricas e lista de posts."""
    # Debug info
    print(f"🌍 DOMÍNIO: {request.get_host()} | SCHEMA: {connection.schema_name}")

    connected_accounts = SocialAccount.objects.all()
    clients = Client.objects.all()
    all_posts_history = SocialPost.objects.all().select_related('client').order_by('-created_at')

    context = {
        'connected_accounts': connected_accounts,
        'clients': clients,
        'posts_history': all_posts_history,
    }
    return render(request, 'projects/social_dashboard.html', context)

# ==============================================================================
# 2. CLIENTES E PROJETOS
# ==============================================================================

@login_required
def client_list_create(request):
    clients = Client.objects.all()
    add_client_form = ClientForm()
    project_form = ProjectForm(tenant=request.tenant) 

    context = {
        'clients': clients,
        'add_client_form': add_client_form,
        'project_form': project_form,
    }
    return render(request, 'projects/client_list.html', context)

@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    all_projects = client.projects.all()

    context = {
        'client': client,
        'projects_andamento': all_projects.filter(status='em_andamento'),
        'projects_finalizados': all_projects.filter(status='finalizado'),
    }
    return render(request, 'projects/client_detail.html', context)

@login_required
def client_detail_api(request, pk):
    """Retorna HTML do modal de detalhes."""
    client = get_object_or_404(Client, pk=pk)
    all_projects = client.projects.all()

    context = {
        'client': client,
        'projects_andamento': all_projects.filter(status='em_andamento'),
        'projects_finalizados': all_projects.filter(status='finalizado'),
    }
    return render(request, 'projects/client_detail_modal.html', context)

@login_required
def get_client_data_api(request, pk):
    """JSON para preencher formulário de edição."""
    client = get_object_or_404(Client, pk=pk)
    connected_platforms = list(client.social_accounts.filter(is_active=True).values_list('platform', flat=True))
    
    data = {
        'id': client.id,
        'name': client.name,
        'cnpj': client.cnpj,
        'nome_representante': client.nome_representante,
        'celular_representante': client.celular_representante,
        'email_representante': client.email_representante,
        'data_inicio_contrato': client.data_inicio_contrato.strftime('%Y-%m-%d') if client.data_inicio_contrato else '',
        'data_finalizacao_contrato': client.data_finalizacao_contrato.strftime('%Y-%m-%d') if client.data_finalizacao_contrato else '',
        'is_active': client.is_active,
        'connected_platforms': connected_platforms,
    }
    return JsonResponse(data)

@login_required
def get_clients_list_api(request):
    clients = Client.objects.all().values('id', 'name')
    return JsonResponse({'clients': list(clients)})

@login_required
def client_metrics_dashboard(request, pk):
    client = get_object_or_404(Client, pk=pk)
    
    # Tarefas
    tasks = Task.objects.filter(project__client=client)
    tasks_avulsas = Task.objects.filter(social_post__client=client)
    all_client_tasks = (tasks | tasks_avulsas).distinct()
    
    task_status_counts = all_client_tasks.values('status').annotate(count=models.Count('id'))
    task_chart_data = {item['status']: item['count'] for item in task_status_counts}

    # Posts Sociais
    posts = client.social_posts.all()
    posts_by_status = posts.values('approval_status').annotate(count=models.Count('id'))
    post_chart_data = {item['approval_status']: item['count'] for item in posts_by_status}
    
    total_likes = posts.aggregate(models.Sum('likes_count'))['likes_count__sum'] or 0
    total_views = posts.aggregate(models.Sum('views_count'))['views_count__sum'] or 0

    context = {
        'client': client,
        'task_chart_data': json.dumps(task_chart_data),
        'post_chart_data': json.dumps(post_chart_data),
        'total_projects': client.projects.count(),
        'total_tasks': all_client_tasks.count(),
        'total_posts': posts.count(),
        'total_likes': total_likes,
        'total_views': total_views,
    }
    return render(request, 'projects/client_metrics.html', context)

@login_required
@require_POST
def create_client_api(request):
    """API exclusiva para CRIAR cliente."""
    form = ClientForm(request.POST, request.FILES)
    if form.is_valid():
        client = form.save()
        return JsonResponse({
            'status': 'success',
            'message': 'Cliente cadastrado com sucesso!',
            'client_id': client.id
        })
    return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@login_required
@require_POST
def update_client_api(request, pk):
    client = get_object_or_404(Client, pk=pk)
    form = ClientForm(request.POST, request.FILES, instance=client)
    
    if form.is_valid():
        client = form.save()
        return JsonResponse({
            'status': 'success', 
            'message': 'Cliente atualizado com sucesso!'
        })
    return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@login_required
@require_POST
def delete_client_api(request, pk):
    """API exclusiva para DELETAR cliente."""
    client = get_object_or_404(Client, pk=pk)
    client.delete()
    return JsonResponse({'status': 'success', 'message': 'Cliente removido.'})

@method_decorator(csrf_exempt, name='dispatch')
class AddProjectAPI(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = ProjectForm(request.POST, tenant=request.tenant) 
        if form.is_valid():
            project = form.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Projeto criado com sucesso!',
                'project': {'id': project.id, 'name': project.name}
            }, status=201)
        return JsonResponse({'status': 'error', 'message': 'Erro ao validar formulário', 'errors': form.errors}, status=400)

# ==============================================================================
# 3. KANBAN E TAREFAS
# ==============================================================================

@login_required
def kanban_view(request, kanban_type='general'):
    if kanban_type == 'operational':
        stages = [
            ('briefing', 'Briefing'),
            ('copy', 'Copy'),
            ('design', 'Design'),
            ('internal_approval', 'Aprovação Interna'),
            ('client_approval', 'Aprovação Cliente'),
            ('scheduling', 'Agendamento'),
            ('published', 'Publicado'),
        ]
        template = 'projects/operational_kanban.html'
        kanban_title = 'Kanban Operacional'
    else:
        stages = [
            ('todo', 'A Fazer'), 
            ('doing', 'Em Andamento'), 
            ('done', 'Concluído')
        ]
        template = 'projects/general_kanban.html'
        kanban_title = 'Kanban Geral'

    tasks = Task.objects.filter(kanban_type=kanban_type).order_by('order')
    
    kanban_data = {}
    for key, label in stages:
        stage_tasks = tasks.filter(status=key)
        kanban_data[key] = [task.to_dict() for task in stage_tasks]

    context = {
        'kanban_data': kanban_data,
        'kanban_data_json': json.dumps(kanban_data),
        'stages': stages,
        'projects': Project.objects.all(),
        'clients': Client.objects.all(),
        'agency_users': CustomUser.objects.filter(agency=request.tenant),
        'kanban_type': kanban_type,
        'kanban_title': kanban_title,
    }
    return render(request, template, context)

@login_required
def kanban_board(request):
    """View alternativa para Kanban Geral."""
    projects = Project.objects.all().prefetch_related('tasks')
    kanban_data = {'todo': [], 'doing': [], 'done': []}

    for project in projects:
        for task in project.tasks.all():
            if task.status in kanban_data:
                kanban_data[task.status].append({
                    'id': task.id,
                    'title': task.title,
                    'description': task.description,
                    'project_name': project.name,
                    'status': task.status,
                    'assigned_to_username': task.assigned_to.username if task.assigned_to else None,
                    'assigned_to_initials': task.assigned_to.username[0].upper() if task.assigned_to else '?'
                })

    context = {
        'projects': projects,
        'kanban_data': json.dumps(kanban_data),
        'agency_users': request.tenant.users.all()
    }
    return render(request, 'projects/kanban_board.html', context)

@login_required
def operational_kanban_board(request):
    """Kanban específico para fluxo de postagens."""
    OPERATIONAL_STAGES_LIST = [
        ('briefing', 'Briefing'),
        ('copy', 'Copy'),
        ('design', 'Design'),
        ('internal_approval', 'Aprovação Interna'),
        ('client_approval', 'Aprovação Cliente'),
        ('scheduling', 'Agendamento da Postagem'),
    ]

    kanban_data = {}
    for stage_value, stage_label in OPERATIONAL_STAGES_LIST:
        tasks = Task.objects.filter(
            kanban_type='operational', 
            status=stage_value
        ).select_related('client', 'social_post').order_by('order', 'priority')
        
        kanban_data[stage_value] = {
            'label': stage_label,
            'tasks': tasks,
            'status_slug': stage_value 
        }
    
    context = {
        'kanban_data': kanban_data,
        'stages': OPERATIONAL_STAGES_LIST,
        'kanban_title': 'Kanban Operacional'
    }
    return render(request, 'projects/operational_kanban_board.html', context)

@login_required
def get_task_details_api(request, pk):
    try:
        task = get_object_or_404(Task, pk=pk)
        return JsonResponse(task.to_dict())
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=404)

@method_decorator(csrf_exempt, name='dispatch')
class AddTaskAPI(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            title = data.get('title')
            project_id = data.get('project')
            assigned_to_id = data.get('assigned_to')
            kanban_type = data.get('kanban_type', 'general')

            if not title:
                return JsonResponse({'status': 'error', 'message': 'Título é obrigatório.'}, status=400)

            project = get_object_or_404(Project, id=project_id) if project_id else None
            
            assigned_user = None
            if assigned_to_id:
                try:
                    assigned_user = request.tenant.users.get(id=assigned_to_id)
                except CustomUser.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Usuário não encontrado.'}, status=404)

            max_order = Task.objects.filter(
                kanban_type=kanban_type,
                status='todo' if kanban_type == 'general' else 'briefing'
            ).aggregate(models.Max('order'))['order__max']
            new_order = (max_order if max_order is not None else -1) + 1

            task = Task.objects.create(
                kanban_type=kanban_type,
                status='todo' if kanban_type == 'general' else 'briefing',
                project=project,
                title=title,
                description=data.get('description'),
                order=new_order,
                created_by=request.user,
                assigned_to=assigned_user
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Tarefa criada!',
                'id': task.id,
                'title': task.title,
                'project_name': project.name if project else '',
                'assigned_to_initials': task.assigned_to.username[0].upper() if task.assigned_to else '?',
                **task.to_dict()
            }, status=201)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class AddOperationalTaskAPI(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        try:
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            project_id = request.POST.get('project')
            client_id = request.POST.get('client') 
            assigned_to_id = request.POST.get('assigned_to')
            reference_image = request.FILES.get('reference_image')

            if not title:
                return JsonResponse({'status': 'error', 'message': 'O título é obrigatório.'}, status=400)

            project = None
            client = None

            if project_id:
                project = get_object_or_404(Project, id=project_id)
                client = project.client
            elif client_id:
                client = get_object_or_404(Client, id=client_id)

            if not client:
                return JsonResponse({'status': 'error', 'message': 'Cliente é obrigatório.'}, status=400)

            # 1. Cria Social Post
            social_post = SocialPost.objects.create(
                client=client,
                caption=description, 
                media_file=reference_image, 
                created_by=request.user,
                approval_status='draft'
            )

            # 2. Cria Tarefa
            max_order = Task.objects.filter(kanban_type='operational', status='briefing').aggregate(models.Max('order'))['order__max']
            new_order = (max_order if max_order is not None else -1) + 1

            task = Task.objects.create(
                kanban_type='operational',
                status='briefing',
                project=project,
                social_post=social_post,
                title=title,
                description=description,
                order=new_order,
                created_by=request.user,
                assigned_to_id=assigned_to_id or None
            )

            return JsonResponse({'status': 'success', 'message': 'Demanda iniciada!', 'task': task.to_dict()}, status=201)

        except Exception as e:
            print(f"Erro AddOperationalTask: {e}")
            return JsonResponse({'status': 'error', 'message': f"Erro interno: {str(e)}"}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class KanbanUpdateTask(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            task_id = data.get('taskId')
            new_status = data.get('newStatus')
            new_order_list = data.get('newOrderList')

            # Validação básica de status
            valid_status_values = [s[0] for s in (GENERAL_STAGES + OPERATIONAL_STAGES + [('published', 'Published')])]
            if new_status not in valid_status_values:
                return JsonResponse({'status': 'error', 'message': 'Status inválido.'}, status=400)

            task = get_object_or_404(Task, id=task_id)
            task.status = new_status
            task.save()

            if new_order_list:
                for index, item_id in enumerate(new_order_list):
                    Task.objects.filter(id=item_id).update(order=index)

            return JsonResponse({'status': 'success', 'message': 'Tarefa atualizada!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class DeleteTaskAPI(View):
    @method_decorator(login_required)
    def delete(self, request, pk, *args, **kwargs):
        try:
            task = get_object_or_404(Task, pk=pk)
            task.delete()
            return JsonResponse({'status': 'success', 'message': 'Tarefa excluída!'}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

# ==============================================================================
# 4. CALENDÁRIO
# ==============================================================================

@login_required
def calendar_view(request):
    """Renderiza a página HTML do calendário."""
    return render(request, 'projects/calendar.html')

@login_required
def get_calendar_events(request):
    """API para buscar eventos filtrados."""
    year = request.GET.get('year')
    month = request.GET.get('month')

    events = CalendarEvent.objects.filter(date__year=year, date__month=month)
    
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title or event.client.name, # Usa nome do cliente se título vazio
            'date': event.date.strftime('%Y-%m-%d'),
            'time': event.time.strftime('%H:%M'),
            'brandName': event.client.name,
            # Tenta pegar logo ou gera iniciais
            'brandLogo': event.client.logo.url if event.client.logo else f"https://ui-avatars.com/api/?name={event.client.name}&background=random",
            'platform': event.platform,
            'type': event.post_type,
            'status': event.status,
            'image': event.media.url if event.media else None, # URL real da imagem
            'description': event.caption or ''
        })

    return JsonResponse(events_data, safe=False)

@login_required
def get_clients_for_select(request):
    """API simples para preencher o dropdown do modal."""
    clients = Client.objects.filter(is_active=True).values('id', 'name')
    return JsonResponse(list(clients), safe=False)

@login_required
@csrf_exempt
def add_calendar_event(request):
    """API para criar post com upload de arquivo."""
    if request.method == 'POST':
        try:
            # Quando tem arquivo, os dados vêm em request.POST e request.FILES
            client_id = request.POST.get('client_id')
            date = request.POST.get('date')
            time = request.POST.get('time')
            platform = request.POST.get('platform')
            status = request.POST.get('status')
            caption = request.POST.get('caption')
            media_file = request.FILES.get('media') # O arquivo vem aqui

            client = Client.objects.get(id=client_id)

            new_event = CalendarEvent.objects.create(
                client=client,
                title=f"Post {client.name}", # Título automático ou adicione campo
                date=date,
                time=time,
                platform=platform,
                status=status,
                caption=caption,
                media=media_file
            )
            
            return JsonResponse({'message': 'Post criado!', 'id': new_event.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Método inválido'}, status=405)

# ==============================================================================
# 5. ESTÚDIO DE CRIAÇÃO E POSTS SOCIAIS
# ==============================================================================

@login_required
def create_post_studio_view(request):
    """
    Renderiza a tela cheia de criação de posts (O Estúdio).
    """
    clients = Client.objects.all()
    clients_map = {}
    
    # 1. Monta o Mapa de contas
    for client in clients:
        accounts = client.social_accounts.all()
        acct_dict = {}
        for acc in accounts:
            acct_dict[acc.platform] = {
                'id': acc.id, 
                'name': acc.account_name, 
                'platform': acc.platform
            }
        clients_map[client.id] = acct_dict

    # 2. Verifica se veio um cliente pré-selecionado da URL (?client_id=1)
    pre_selected_id = request.GET.get('client_id')
    selected_client_obj = None

    if pre_selected_id:
        # --- AQUI ESTAVA FALTANDO: Buscamos o objeto real no banco ---
        selected_client_obj = Client.objects.filter(id=pre_selected_id).first()
    
    context = {
        'clients': clients,
        'clients_map_json': json.dumps(clients_map), 
        'pre_selected_client_id': int(pre_selected_id) if pre_selected_id else None,
        
        # --- ENVIAMOS O OBJETO PARA O TEMPLATE ---
        'selected_client': selected_client_obj, 
        
        'connected_accounts': SocialAccount.objects.all()
    }
    return render(request, 'projects/create_post_studio.html', context)

@method_decorator(csrf_exempt, name='dispatch')
class CreateSocialPostAPI(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        try:
            data = request.POST
            content = data.get('content')
            scheduled_at_str = data.get('scheduled_for')
            client_id = data.get('client')
            image_file = request.FILES.get('image')
            account_ids = data.getlist('accounts') 

            if not content or not scheduled_at_str or not client_id:
                 return JsonResponse({'status': 'error', 'message': 'Preencha cliente, conteúdo e data.'}, status=400)

            client = get_object_or_404(Client, pk=client_id)
            
            try:
                scheduled_for = datetime.datetime.strptime(scheduled_at_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Data inválida.'}, status=400)

            # 1. Cria Post
            post = SocialPost.objects.create(
                client=client,
                caption=content,
                scheduled_for=scheduled_for,
                image=image_file,
                approval_status='draft',
                created_by=request.user
            )

            # 2. Vincula Contas
            if account_ids:
                accounts = SocialAccount.objects.filter(id__in=account_ids)
                for acc in accounts:
                    fmt = 'video' if acc.platform in ['tiktok', 'youtube'] else 'feed'
                    SocialPostDestination.objects.create(post=post, account=acc, format_type=fmt)

            # 3. Cria Tarefa no Kanban
            max_order = Task.objects.filter(kanban_type='operational', status='briefing').aggregate(models.Max('order'))['order__max']
            new_order = (max_order if max_order is not None else -1) + 1

            Task.objects.create(
                kanban_type='operational',
                status='briefing',
                title=f"Post: {client.name} - {scheduled_for.strftime('%d/%m')}",
                description=content[:150],
                social_post=post,
                created_by=request.user,
                order=new_order
            )

            return JsonResponse({'status': 'success', 'message': 'Post criado e tarefa gerada!', 'id': post.id}, status=201)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Erro interno: {str(e)}'}, status=500)

# ==============================================================================
# 6. APROVAÇÃO EXTERNA
# ==============================================================================

@login_required
def send_approval_link(request, post_id):
    post = get_object_or_404(SocialPost, id=post_id)
    
    if not post.approval_token:
        post.approval_token = secrets.token_hex(16)
        post.save()
        
    approval_url = request.build_absolute_uri(
        reverse('external_approval_view', kwargs={'token': post.approval_token})
    )
    
    # Avança no Kanban se necessário
    try:
        task = post.task # OneToOne
        if task and task.status == 'internal_approval':
            task.status = 'client_approval'
            task.save()
    except Exception:
        pass 

    return JsonResponse({
        'status': 'success', 
        'message': 'Link gerado.',
        'approval_url': approval_url
    })

def external_approval_view(request, token):
    """View Pública."""
    post = get_object_or_404(SocialPost, approval_token=token)
    context = {
        'post': post,
        'media_url': post.media_file.url if post.media_file else '',
    }
    return render(request, 'projects/external_approval.html', context)

@csrf_exempt
def approval_action(request):
    """Endpoint simplificado para ações externas (se necessário)."""
    if request.method == 'POST':
        return JsonResponse({'status': 'pending', 'message': 'Use ProcessApprovalAction.'})
    return JsonResponse({'status': 'error', 'message': 'Método inválido.'}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ProcessApprovalAction(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            token = data.get('token')
            action = data.get('action') 
            feedback = data.get('feedback', '')
            image_data = data.get('image_data')

            post = get_object_or_404(SocialPost, approval_token=token)
            
            try:
                task = post.task
            except Task.DoesNotExist:
                task = None

            if action == 'approve':
                post.approval_status = 'approved_to_schedule'
                if task: task.status = 'scheduling'

            elif action == 'reject_copy':
                post.approval_status = 'copy_review'
                post.feedback_text = feedback
                if task: task.status = 'copy'

            elif action == 'reject_design':
                post.approval_status = 'design_review'
                post.feedback_text = feedback
                
                if image_data:
                    # Decodifica base64 da imagem rabiscada
                    format_str, imgstr = image_data.split(';base64,') 
                    ext = format_str.split('/')[-1] 
                    file_name = f"feedback_design_{post.id}.{ext}"
                    post.feedback_image_markup = image_data # Salvando string base64 ou converter para File
                
                if task: task.status = 'design'

            if task: task.save()
            post.save()
            
            return JsonResponse({'status': 'success', 'message': 'Feedback registrado!'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

# ==============================================================================
# 7. AUTENTICAÇÃO SOCIAL (OAUTH)
# ==============================================================================

@login_required
def meta_auth_start(request, client_id):
    request.session['meta_connect_client_id'] = client_id
    state = secrets.token_urlsafe(16)
    request.session['meta_oauth_state'] = state
    
    service = MetaService()
    url = service.get_auth_url(state)
    return redirect(url)

@login_required
def meta_auth_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    if not state or state != request.session.get('meta_oauth_state'):
        messages.error(request, "Erro CSRF no Facebook.")
        return redirect('social_dashboard')
    
    client_id = request.session.get('meta_connect_client_id')
    client = get_object_or_404(Client, pk=client_id)
    
    current_domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    callback_url = f"{protocol}://{current_domain}/meta-callback/"

    service = MetaService()
    # Requisição manual para troca de token
    token_url = (
        f"https://graph.facebook.com/v19.0/oauth/access_token?"
        f"client_id={settings.META_APP_ID}&"
        f"redirect_uri={callback_url}&"
        f"client_secret={settings.META_APP_SECRET}&"
        f"code={code}"
    )
    
    resp = requests.get(token_url)
    token_data = resp.json()

    if 'access_token' in token_data:
        accounts = service.get_user_pages(token_data['access_token'], client)
        if not accounts:
            messages.warning(request, "Nenhuma página encontrada.")
        else:
            messages.success(request, f"{len(accounts)} páginas conectadas.")
    else:
        error_msg = token_data.get('error', {}).get('message', 'Erro desconhecido')
        messages.error(request, f"Erro Facebook: {error_msg}")
        
    return redirect('social_dashboard')

@login_required
def linkedin_auth_start(request, client_id):
    request.session['linkedin_client_id'] = client_id
    state = secrets.token_urlsafe(16)
    request.session['linkedin_oauth_state'] = state
    
    service = LinkedInService()
    return redirect(service.get_auth_url(state))

@login_required
def linkedin_auth_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')

    if error:
        messages.error(request, f"Erro LinkedIn: {error}")
        return redirect('social_dashboard')

    if not state or state != request.session.get('linkedin_oauth_state'):
        messages.error(request, "Erro CSRF no LinkedIn.")
        return redirect('social_dashboard')

    client_id = request.session.get('linkedin_client_id')
    client = get_object_or_404(Client, pk=client_id)

    service = LinkedInService()
    token_data = service.exchange_code_for_token(code)

    if 'access_token' in token_data:
        account = service.save_account(token_data, client)
        if account:
            messages.success(request, f"LinkedIn conectado: {account.account_name}")
        else:
            messages.error(request, "Erro ao salvar perfil LinkedIn.")
    else:
        messages.error(request, "Erro ao obter token LinkedIn.")

    return redirect('social_dashboard')

@login_required
def tiktok_auth_start(request, client_id):
    request.session['tiktok_client_id'] = client_id 
    state = secrets.token_urlsafe(16)
    request.session['tiktok_oauth_state'] = state
    
    service = TikTokService()
    return redirect(service.get_auth_url(state))

@login_required
def tiktok_auth_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')
    saved_state = request.session.get('tiktok_oauth_state')
    client_id = request.session.get('tiktok_client_id')

    if not state or state != saved_state:
        messages.error(request, "Erro CSRF no TikTok")
        return redirect('social_dashboard')

    if code:
        service = TikTokService()
        token_data = service.get_access_token(code)
        
        if token_data and 'access_token' in token_data:
            client = get_object_or_404(Client, id=client_id)
            user_info = service.get_user_info(token_data['access_token'])
            account_name = user_info['name'] if user_info else "TikTok Account"

            SocialAccount.objects.update_or_create(
                account_id=token_data.get('open_id'),
                platform='tiktok',
                defaults={
                    'client': client,
                    'access_token': token_data['access_token'],
                    'refresh_token': token_data.get('refresh_token'),
                    'account_name': account_name,
                    'is_active': True,
                }
            )
            return render(request, 'projects/auth_success_popup.html')
            
    return redirect('social_dashboard')