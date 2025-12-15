from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import models # Para usar models.Max
from django.urls import reverse
from django.conf import settings
import json
from django.contrib import messages
import datetime
from django.utils import timezone
import secrets
from django.contrib.auth import views as auth_views
from .models import Task, CalendarEvent, Project, Client, SocialPost, SocialAccount, SocialPostDestination
from .forms import ClientForm, TenantAuthenticationForm, ProjectForm
from accounts.models import CustomUser
import secrets
from django.shortcuts import redirect
from .services import MetaService, LinkedInService, TikTokService
from django.db import connection

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

@login_required
def kanban_view(request, kanban_type='general'):
    # 1. Define as colunas e o título baseados no tipo
    if kanban_type == 'operational':
        stages = [
            ('briefing', 'Briefing'),
            ('copy', 'Copy'),
            ('design', 'Design'),
            ('internal_approval', 'Aprovação Interna'),
            ('client_approval', 'Aprovação Cliente'),
            ('scheduling', 'Agendamento'),
            ('published', 'Publicado'), # Adicionei publicado para completar o ciclo
        ]
        template = 'projects/operational_kanban.html'
        kanban_title = 'Kanban Operacional' # <-- Definido aqui
    else:
        stages = [
            ('todo', 'A Fazer'), 
            ('doing', 'Em Andamento'), 
            ('done', 'Concluído')
        ]
        template = 'projects/general_kanban.html'
        kanban_title = 'Kanban Geral' # <-- Definido aqui

    # 2. Busca tarefas APENAS desse tipo
    tasks = Task.objects.filter(kanban_type=kanban_type).order_by('order')
    
    # 3. Organiza os dados
    kanban_data = {}
    for key, label in stages:
        stage_tasks = tasks.filter(status=key)
        kanban_data[key] = [task.to_dict() for task in stage_tasks]

   # Busca usuários da agência
    agency_users = CustomUser.objects.filter(agency=request.tenant)
    
    # --- VERIFIQUE SE ESTA LINHA EXISTE E ESTÁ CORRETA ---
    projects_list = Project.objects.all() 
    # -----------------------------------------------------

    context = {
        'kanban_data': kanban_data, # (ou json.dumps, dependendo da sua versão anterior)
        'kanban_data_json': json.dumps(kanban_data),
        'stages': stages,
        
        'projects': projects_list, # <--- ESSA VARIÁVEL É CRÍTICA
        'clients': Client.objects.all(),
        'agency_users': agency_users,
        'kanban_type': kanban_type,
        'kanban_title': kanban_title,
    }
    return render(request, template, context)

# ATUALIZE KanbanUpdateTask para usar os novos status
@method_decorator(csrf_exempt, name='dispatch')
class KanbanUpdateTask(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        
        valid_status_values = [s[0] for s in (GENERAL_STAGES + OPERATIONAL_STAGES)]
        if new_status not in valid_status_values:
             return JsonResponse({'status': 'error', 'message': 'Status inválido.'}, status=400)
    pass

@login_required
def dashboard(request):
    today = datetime.date.today()

    # 1. Cards de Estatísticas
    project_count = Project.objects.count()
    pending_tasks_count = Task.objects.filter(status__in=['todo', 'in_progress']).count()
    completed_tasks_count = Task.objects.filter(status='done').count()
    total_tasks = pending_tasks_count + completed_tasks_count
    completion_percent = (completed_tasks_count / total_tasks * 100) if total_tasks else 0
    completion_percent = round(completion_percent)
    status_counts = Task.objects.values('status').annotate(count=models.Count('id'))
    chart_status_data = {item['status']: item['count'] for item in status_counts}

    posts_metrics = {
        'scheduled': SocialPost.objects.filter(scheduled_for__gte=timezone.now()).count(),
        'published': SocialPost.objects.filter(scheduled_for__lt=timezone.now()).count(),
        'pending_approval': Task.objects.filter(status='client_approval').count()
    }

    # 2. Widget de Eventos Futuros (Assumindo que está funcionando)
    upcoming_events = CalendarEvent.objects.filter(start_date__gte=today).order_by('start_date')[:5]
    recent_tasks = Task.objects.filter(status__in=['todo', 'in_progress']).order_by('-created_at')[:5]

    context = {
        'project_count': project_count,
        'pending_tasks_count': pending_tasks_count,
        'completed_tasks_count': completed_tasks_count,
        'total_tasks': total_tasks, # NOVO: Total de tarefas
        'completion_percent': completion_percent,
        'upcoming_events': upcoming_events,
        'recent_tasks': recent_tasks,
        'chart_status_data': json.dumps(chart_status_data),
        'posts_metrics': json.dumps(posts_metrics),
    }

    return render(request, 'projects/dashboard.html', context)
pass

@login_required
def kanban_board(request):
    projects = Project.objects.all().prefetch_related('tasks')

    kanban_data = {
        'todo': [],
        'doing': [],
        'done': [],
    }

    for project in projects:
        for task in project.tasks.all(): # tasks já está ordenada por 'order'
            kanban_data[task.status].append({
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'project_name': project.name, # Para exibir o projeto no card
                'status': task.status,
                'assigned_to_username': task.assigned_to.username if task.assigned_to else None,
                'assigned_to_initials': task.assigned_to.username[0].upper() if task.assigned_to else '?'
            })

    context = {
        'projects': projects, # Passa todos os projetos para o select de criação
        'kanban_data': json.dumps(kanban_data), # Serializa para JSON para o JS
        'agency_users': request.tenant.users.all()
    }
    return render(request, 'projects/kanban_board.html', context)
pass
@login_required
def get_task_details_api(request, pk):
    try:
        # Pega a tarefa (o modelo Task é do tenant, então já é seguro)
        task = get_object_or_404(Task, pk=pk)
        # Retorna os dados formatados pela função to_dict
        return JsonResponse(task.to_dict())
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=404)
pass

# --- NOVA API PARA DELETAR TAREFA ---
@method_decorator(csrf_exempt, name='dispatch')
class DeleteTaskAPI(View):
    @method_decorator(login_required)
    def delete(self, request, pk, *args, **kwargs):
        try:
            task = get_object_or_404(Task, pk=pk)
            # (Opcional: adicione uma checagem se request.user == task.created_by)
            task.delete()
            return JsonResponse({'status': 'success', 'message': 'Tarefa excluída com sucesso!'}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    pass

# API para atualizar o status e a ordem de uma tarefa

@method_decorator(csrf_exempt, name='dispatch') # Temporário para API
class AddTaskAPI(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            title = data.get('title')
            description = data.get('description')
            project_id = data.get('project') # Pode vir vazio agora
            assigned_to_id = data.get('assigned_to')
            kanban_type = data.get('kanban_type', 'general') # Novo campo

            if not title:
                return JsonResponse({'status': 'error', 'message': 'Título é obrigatório.'}, status=400)

            project = None
            if project_id:
                project = get_object_or_404(Project, id=project_id)
            assigned_user = None
            if assigned_to_id:
                # Busca o usuário no schema PÚBLICO
                try:
                    assigned_user = request.tenant.users.get(id=assigned_to_id)
                except CustomUser.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Usuário atribuído não encontrado.'}, status=404)

            max_order = Task.objects.filter(
                kanban_type=kanban_type, # Filtra pelo tipo correto!
                status='todo' if kanban_type == 'general' else 'briefing'
            ).aggregate(models.Max('order'))['order__max']
            new_order = (max_order if max_order is not None else -1) + 1

            task = Task.objects.create(
                kanban_type=kanban_type, # Salva o tipo
                status='todo' if kanban_type == 'general' else 'briefing',
                project=project, # Pode ser None se seu Model permitir
                title=title,
                description=description,
                order=new_order,
                created_by=request.user,
                assigned_to=assigned_user
            )

            # Retorna os dados da nova tarefa para o frontend
            return JsonResponse({
                'status': 'success',
                'message': 'Tarefa criada com sucesso!',
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'project_name': project.name,
                'status': task.status,
                'order': task.order,
                'assigned_to_username': task.assigned_to.username if task.assigned_to else None,
                'assigned_to_initials': task.assigned_to.username[0].upper() if task.assigned_to else '?',
                **task.to_dict()
            }, status=201)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    pass
@method_decorator(csrf_exempt, name='dispatch') # TEMPORÁRIO: Desabilita CSRF para a API POST
class KanbanUpdateTask(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            task_id = data.get('taskId')
            new_status = data.get('newStatus')
            new_order_list = data.get('newOrderList') # Lista de IDs na nova ordem

            task = get_object_or_404(Task, id=task_id)

            # Atualiza o status
            task.status = new_status
            task.save()

            # Atualiza a ordem das tarefas na coluna
            for index, item_id in enumerate(new_order_list):
                Task.objects.filter(id=item_id).update(order=index)

            return JsonResponse({'status': 'success', 'message': 'Tarefa atualizada com sucesso!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    pass
@login_required
def operational_kanban_board(request):
    """
    Kanban focado no fluxo de trabalho de postagens operacionais (Briefing -> Agendamento).
    """
    # Define as colunas do seu fluxo operacional
    OPERATIONAL_STAGES = [
        ('briefing', 'Briefing'),
        ('copy', 'Copy'),
        ('design', 'Design'),
        ('internal_approval', 'Aprovação Interna'),
        ('client_approval', 'Aprovação Cliente'),
        ('scheduling', 'Agendamento da Postagem'),
    ]

    kanban_data = {}
    for stage_value, stage_label in OPERATIONAL_STAGES:
        # Filtra tarefas do tipo 'operational' e com o status específico
        tasks = Task.objects.filter(
            kanban_type='operational', 
            status=stage_value
        ).select_related('client', 'social_post').order_by('priority')
        
        kanban_data[stage_value] = {
            'label': stage_label,
            'tasks': tasks,
            'status_slug': stage_value 
        }
    
    context = {
        'kanban_data': kanban_data,
        'stages': OPERATIONAL_STAGES,
        'kanban_title': 'Kanban Operacional'
    }
    # NOTA: Você precisará criar o template 'projects/operational_kanban_board.html'
    return render(request, 'projects/operational_kanban_board.html', context)
pass
@login_required
def calendar_view(request):
   
    return render(request, 'projects/calendar.html')
pass
@login_required
def get_calendar_events(request):
    """
    Retorna todos os eventos de um mês/ano específico como JSON.
    """
    # Pega os parâmetros da URL (ex: ?year=2025&month=10)
    year = request.GET.get('year')
    month = request.GET.get('month')

    if not year or not month:
        return JsonResponse({'error': 'Ano e Mês são obrigatórios'}, status=400)

    # Filtra os eventos do usuário para aquele mês e ano
    events = CalendarEvent.objects.filter(
        created_by=request.user,
        start_date__year=year,
        start_date__month=month
    )

    # Converte os eventos para um formato que o JS entende
    events_list = [event.to_dict() for event in events]

    return JsonResponse(events_list, safe=False)
pass

# projects/views.py

@login_required
@require_POST
def add_calendar_event(request):
    """
    Cria um novo evento no banco de dados.
    """
    try:
        data = json.loads(request.body)

        title = data.get('title')
        date_str = data.get('date') # Formato 'YYYY-MM-DD'

        if not title or not date_str:
            return JsonResponse({'error': 'Título e Data são obrigatórios'}, status=400)

        # --- CORREÇÃO AQUI ---
        # Converte a string de data (ex: "2025-11-15") em um objeto de data
        try:
            event_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            return JsonResponse({'error': 'Formato de data inválido. Use YYYY-MM-DD'}, status=400)
        # --- FIM DA CORREÇÃO ---

        # Cria o evento e liga ao usuário logado
        event = CalendarEvent.objects.create(
            title=title,
            start_date=event_date, # <-- Usa o objeto de data, não a string
            created_by=request.user
        )

        # Agora event.to_dict() vai funcionar, pois event.start_date é um objeto de data
        return JsonResponse(event.to_dict(), status=201)

    except Exception as e:
        # Captura o erro 'strftime' e o envia
        return JsonResponse({'error': str(e)}, status=500)
pass
@login_required
def client_list_create(request):
    """
    Página para listar clientes e exibir o formulário para o modal.
    """
    clients = Client.objects.all()
    add_client_form = ClientForm()
    project_form = ProjectForm(tenant=request.tenant) 

    context = {
        'clients': clients,
        'add_client_form': add_client_form,
        'project_form': project_form,
    }
    return render(request, 'projects/client_list.html', context)
pass

@login_required
def client_metrics_dashboard(request, pk):
    client = get_object_or_404(Client, pk=pk)
    
    # --- 1. DADOS DE TAREFAS (Para Gráfico de Pizza) ---
    tasks = Task.objects.filter(project__client=client) # Tarefas ligadas a projetos do cliente
    # Se quiser incluir tarefas operacionais avulsas ligadas via social_post:
    tasks_avulsas = Task.objects.filter(social_post__client=client)
    
    # União de querysets (distinct para evitar duplicatas se houver sobreposição)
    all_client_tasks = (tasks | tasks_avulsas).distinct()
    
    task_status_counts = all_client_tasks.values('status').annotate(count=models.Count('id'))
    # Formata: {'todo': 10, 'doing': 5}
    task_chart_data = {item['status']: item['count'] for item in task_status_counts}

    # --- 2. DADOS SOCIAIS (Para Gráfico de Barras) ---
    posts = client.social_posts.all()
    posts_by_status = posts.values('approval_status').annotate(count=models.Count('id'))
    post_chart_data = {item['approval_status']: item['count'] for item in posts_by_status}
    
    # Métricas totais (Soma)
    total_likes = posts.aggregate(models.Sum('likes_count'))['likes_count__sum'] or 0
    total_views = posts.aggregate(models.Sum('views_count'))['views_count__sum'] or 0

    context = {
        'client': client,
        'task_chart_data': json.dumps(task_chart_data), # JSON para o JS
        'post_chart_data': json.dumps(post_chart_data), # JSON para o JS
        'total_projects': client.projects.count(),
        'total_tasks': all_client_tasks.count(),
        'total_posts': posts.count(),
        'total_likes': total_likes,
        'total_views': total_views,
    }
    return render(request, 'projects/client_metrics.html', context)

@login_required
def get_client_data_api(request, pk):
    """
    Retorna os dados do cliente em JSON para preencher o modal de edição.
    """
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

# --- NOVA API: OBTER DADOS DO CLIENTE (PARA EDIÇÃO) ---
@method_decorator(csrf_exempt, name='dispatch')
class AddClientAPI(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        # Verifica se é EDICÃO (tem ID) ou CRIAÇÃO
        client_id = request.POST.get('client_id')
        
        if client_id:
            client = get_object_or_404(Client, id=client_id)
            form = ClientForm(request.POST, request.FILES, instance=client)
        else:
            form = ClientForm(request.POST, request.FILES)

        if form.is_valid():
            client = form.save()
            return JsonResponse({
                'status': 'success', 
                'message': 'Cliente salvo com sucesso!',
                'client': {
                    'id': client.id,
                    'name': client.name,
                    'cnpj': client.cnpj,
                    'representative': client.nome_representante,
                    'email': client.email_representante,
                    'status': 'Ativo' if client.is_active else 'Inativo'
                }
            }, status=200)
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@method_decorator(csrf_exempt, name='dispatch') # Para permitir POST do JS
class AddClientAPI(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = ClientForm(request.POST, request.FILES)
        if form.is_valid():
            client = form.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Cliente cadastrado com sucesso!',
                'client': {
                    'id': client.id,
                    'name': client.name,
                    'cnpj': client.cnpj,
                    'nome_representante': client.nome_representante,
                    'email_representante': client.email_representante,
                    'data_finalizacao_contrato': client.data_finalizacao_contrato.strftime('%d/%m/%Y') if client.data_finalizacao_contrato else 'Ativo'
                }
            }, status=201)
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Erro ao validar formulário',
                'errors': form.errors # Retorna os erros do formulário
            }, status=400)
    pass
@login_required
def client_detail_api(request, pk):
    client = get_object_or_404(Client, pk=pk)

    all_projects = client.projects.all()
    projects_andamento = all_projects.filter(status='em_andamento')
    projects_finalizados = all_projects.filter(status='finalizado')

    context = {
        'client': client,
        'projects_andamento': projects_andamento,
        'projects_finalizados': projects_finalizados,
    }
    # Renderiza o template do modal de detalhes e o retorna como HTML
    return render(request, 'projects/client_detail_modal.html', context)
pass
@login_required
def client_detail(request, pk):
    # Busca o cliente pelo ID (pk) ou retorna 404 se não existir
    client = get_object_or_404(Client, pk=pk)

    # Pega todos os projetos deste cliente
    all_projects = client.projects.all()

    # Filtra os projetos por status
    projects_andamento = all_projects.filter(status='em_andamento')
    projects_finalizados = all_projects.filter(status='finalizado')

    context = {
        'client': client,
        'projects_andamento': projects_andamento,
        'projects_finalizados': projects_finalizados,
    }
    return render(request, 'projects/client_detail.html', context)
pass
class TenantLoginView(auth_views.LoginView):
    
    form_class = TenantAuthenticationForm
    template_name = 'projects/login.html'

@method_decorator(csrf_exempt, name='dispatch')
class AddProjectAPI(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):

        # Passa o tenant (agência atual) para o formulário
        form = ProjectForm(request.POST, tenant=request.tenant) 

        if form.is_valid():
            project = form.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Projeto criado com sucesso!',
                'project': {
                    'id': project.id,
                    'name': project.name,
                }
            }, status=201)
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Erro ao validar formulário',
                'errors': form.errors
            }, status=400)
    pass
# projects/views.py

@login_required
def social_dashboard(request):
    """
    Renderiza o painel principal com métricas e lista de posts.
    """

    # --- DEBUG: IMPRIMIR NO TERMINAL ---
    print(f"🌍 DOMÍNIO ACESSADO: {request.get_host()}")
    print(f"📂 SCHEMA ATIVO: {connection.schema_name}")
    print(f"👤 TENANT DETECTADO: {getattr(request, 'tenant', 'Nenhum')}")
    # -----------------------------------

    # 1. Busca dados básicos
    connected_accounts = SocialAccount.objects.all()
    clients = Client.objects.all()
    # 2. Separa posts por status e data
    now = timezone.now()
    
    all_posts_history = SocialPost.objects.all().select_related('client').order_by('-created_at')

    context = {
        'connected_accounts': connected_accounts,
        'clients': clients, # Necessário para o modal de seleção
        'posts_history': all_posts_history, # Histórico unificado
    }
    return render(request, 'projects/social_dashboard.html', context)
    
@login_required
def create_post_studio_view(request):
    """
    Renderiza a tela de criação e envia o mapa de contas de TODOS os clientes.
    """
    clients = Client.objects.all()
    
    # 1. Monta o Mapa: { ID_CLIENTE: { 'facebook': {...}, 'instagram': {...} } }
    clients_map = {}
    
    for client in clients:
        # Pega todas as contas sociais deste cliente
        accounts = client.social_accounts.all()
        acct_dict = {}
        
        for acc in accounts:
            # A chave é a plataforma (ex: 'facebook') para o JS encontrar fácil
            acct_dict[acc.platform] = {
                'id': acc.id,
                'name': acc.account_name,
                'platform': acc.platform
            }
        
        # Guarda no dicionário principal usando o ID do cliente como chave
        clients_map[client.id] = acct_dict

    # 2. Verifica se veio um cliente pré-selecionado da URL (?client_id=1)
    pre_selected = request.GET.get('client_id')
    
    context = {
        'clients': clients,
        # AQUI ESTÁ A MÁGICA: Convertemos o dicionário Python para Texto JSON
        'clients_map_json': json.dumps(clients_map), 
        'pre_selected_client_id': int(pre_selected) if pre_selected else None
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
            
            # IDs das contas selecionadas (checkboxes)
            account_ids = data.getlist('accounts') 

            # Validações
            if not content or not scheduled_at_str or not client_id:
                 return JsonResponse({'status': 'error', 'message': 'Preencha cliente, conteúdo e data.'}, status=400)

            client = get_object_or_404(Client, pk=client_id)
            
            try:
                scheduled_for = datetime.datetime.strptime(scheduled_at_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Data inválida.'}, status=400)

            # 1. CRIAR O SOCIAL POST
            post = SocialPost.objects.create(
                client=client,
                caption=content,
                scheduled_for=scheduled_for,
                image=image_file,
                approval_status='draft', # Começa como Rascunho para ir pro Kanban
                created_by=request.user
            )

            # 2. VINCULAR AS CONTAS (Cria os Destinos)
            if account_ids:
                accounts = SocialAccount.objects.filter(id__in=account_ids)
                
                for acc in accounts:
                    # Lógica inteligente para definir o formato
                    fmt = 'feed'
                    if acc.platform in ['tiktok', 'youtube']: 
                        # Se for youtube, assumimos video por enquanto, ou shorts se for curto
                        # Aqui você pode refinar a lógica no futuro
                        fmt = 'video' 
                    
                    SocialPostDestination.objects.create(
                        post=post, 
                        account=acc, 
                        format_type=fmt
                    )

            # 3. CRIAÇÃO AUTOMÁTICA DA TAREFA NO KANBAN OPERACIONAL
            # Isso é vital: O post vira um card na coluna "Briefing" ou "Copy"
            
            # Pega a ordem máxima
            max_order = Task.objects.filter(
                kanban_type='operational', 
                status='briefing'
            ).aggregate(models.Max('order'))['order__max']
            new_order = (max_order if max_order is not None else -1) + 1

            Task.objects.create(
                kanban_type='operational',
                status='briefing', # Entra no início do fluxo
                title=f"Post: {client.name} - {scheduled_for.strftime('%d/%m')}",
                description=content[:150], # Resumo da legenda
                social_post=post, # VINCULA AO POST
                project=None, 
                created_by=request.user,
                order=new_order
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Post criado! Tarefa enviada para o Kanban Operacional.',
                'id': post.id
            }, status=201)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Erro interno: {str(e)}'}, status=500)
    pass
@login_required
def send_approval_link(request, post_id):
    """
    Endpoint (API) que gera o token, constrói o link público e move o Kanban.
    """
    post = get_object_or_404(SocialPost, id=post_id)
    
    # 1. Gerar Token Seguro se não existir
    if not post.approval_token:
        post.approval_token = secrets.token_hex(16)
        post.save()
        
    # 2. Montar o Link Público
    # Importante: O domínio precisa ser acessível publicamente na produção.
    approval_url = request.build_absolute_uri(
        reverse('external_approval_view', kwargs={'token': post.approval_token})
    )
    
    # 3. Mover o Kanban (Se a Task ligada estiver em 'internal_approval')
    try:
        task = post.task_link.first() 
        if task and task.status == 'internal_approval':
            task.status = 'client_approval' # Move para 'Aprovação Cliente'
            task.save()
            
    except Task.DoesNotExist:
        pass 

    # 4. SIMULAÇÃO DE ENVIO (Na realidade, você chamaria um serviço de e-mail ou SMS)
    # Aqui, apenas retornamos o link para a agência.
    return JsonResponse({
        'status': 'success', 
        'message': 'Link de aprovação gerado e pronto para envio.',
        'approval_url': approval_url
    })
pass
# --- VIEW PÚBLICA DE APROVAÇÃO (SEM NECESSIDADE DE LOGIN) ---

# Requer o token de aprovação para acesso
def external_approval_view(request, token):
    # Busca o post pelo token seguro
    post = get_object_or_404(SocialPost, approval_token=token)
    
    context = {
        'post': post,
        # Passamos a URL da mídia para o JS usar no Canvas
        'media_url': post.media_file.url if post.media_file else '',
    }
    return render(request, 'projects/external_approval.html', context)
pass

@csrf_exempt # Permite POST sem CSRF para links externos
def approval_action(request):
    """
    API para registrar a ação de aprovação/reprovação (chamada do template externo).
    """
    if request.method == 'POST':
        # ... (Lógica de processamento de POST, token, action, feedback) ...
        # (Essa lógica deve ser implementada no próximo passo, focando na segurança e no fluxo)
        return JsonResponse({'status': 'pending', 'message': 'Endpoint de ação pendente de implementação detalhada.'})
    
    return JsonResponse({'status': 'error', 'message': 'Método inválido.'}, status=400)
pass

@method_decorator(csrf_exempt, name='dispatch')
class ProcessApprovalAction(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            token = data.get('token')
            action = data.get('action') # 'approve', 'reject_copy', 'reject_design'
            feedback = data.get('feedback', '')
            image_data = data.get('image_data') # Base64 da imagem rabiscada

            post = get_object_or_404(SocialPost, approval_token=token)
            
            # Encontra a tarefa ligada a este post no Kanban
            task = post.task # Usando o related_name 'task' do OneToOneField

            if action == 'approve':
                # 1. Cliente Aprovou
                post.approval_status = 'approved_to_schedule'
                # Move Kanban para "Agendamento"
                if task:
                    task.status = 'scheduling'
                    task.save()

            elif action == 'reject_copy':
                # 2. Cliente Reprovou Texto
                post.approval_status = 'copy_review'
                post.feedback_text = feedback
                # Move Kanban de volta para "Copy"
                if task:
                    task.status = 'copy'
                    task.save()

            elif action == 'reject_design':
                # 3. Cliente Reprovou Design (Com Rabisco)
                post.approval_status = 'design_review'
                
                # Salva o texto do feedback
                post.feedback_text = feedback # Ou crie um campo feedback_design separado
                
                # Salva a imagem rabiscada (Converte Base64 para Arquivo)
                if image_data:
                    format, imgstr = image_data.split(';base64,') 
                    ext = format.split('/')[-1] 
                    file_name = f"feedback_design_{post.id}.{ext}"
                    data = ContentFile(base64.b64decode(imgstr), name=file_name)
                    
                    # Salva no campo de feedback (se for FileField) ou texto
                    post.feedback_image_markup = image_data # Salvando como texto base64 por enquanto
                
                # Move Kanban de volta para "Design"
                if task:
                    task.status = 'design'
                    task.save()

            post.save()
            
            return JsonResponse({'status': 'success', 'message': 'Feedback registrado e equipe notificada!'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class AddOperationalTaskAPI(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        try:
            # Captura os dados do formulário
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            
            # Tenta pegar Projeto OU Cliente (um dos dois deve existir)
            project_id = request.POST.get('project')
            client_id = request.POST.get('client') 
            
            assigned_to_id = request.POST.get('assigned_to')
            reference_image = request.FILES.get('reference_image')

            # --- VALIDAÇÃO 1: Título Obrigatório ---
            if not title:
                return JsonResponse({'status': 'error', 'message': 'O título é obrigatório.'}, status=400)

            # --- LÓGICA DE VÍNCULO (Quem é o dono?) ---
            project = None
            client = None

            # Cenário A: Usuário selecionou um Projeto
            if project_id:
                try:
                    project = Project.objects.get(id=project_id)
                    client = project.client # Tenta pegar o cliente do projeto
                except Project.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Projeto não encontrado.'}, status=404)

            # Cenário B: Usuário selecionou um Cliente direto (ou Projeto sem cliente)
            if not client and client_id:
                try:
                    client = Client.objects.get(id=client_id)
                except Client.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Cliente não encontrado.'}, status=404)

            # --- VALIDAÇÃO 2: Cliente Obrigatório ---
            # Para criar um SocialPost, PRECISAMOS de um cliente.
            if not client:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'É necessário vincular um Cliente (diretamente ou através de um Projeto) para criar uma demanda de conteúdo.'
                }, status=400)

            # 1. CRIAR O SOCIAL POST
            social_post = SocialPost.objects.create(
                client=client,
                caption=description, 
                media_file=reference_image, 
                created_by=request.user,
                approval_status='draft'
            )

            # 2. CALCULAR A ORDEM NO KANBAN
            max_order = Task.objects.filter(
                kanban_type='operational', 
                status='briefing'
            ).aggregate(models.Max('order'))['order__max']
            new_order = (max_order if max_order is not None else -1) + 1

            # 3. CRIAR A TAREFA
            task = Task.objects.create(
                kanban_type='operational',
                status='briefing',
                project=project, # Pode ser None
                social_post=social_post,
                title=title,
                description=description,
                order=new_order,
                created_by=request.user,
                assigned_to_id=assigned_to_id if assigned_to_id else None
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Demanda iniciada com sucesso!',
                'task': task.to_dict()
            }, status=201)

        except Exception as e:
            # Log do erro real no console do servidor para debug
            print(f"Erro na API AddOperationalTask: {e}")
            return JsonResponse({'status': 'error', 'message': f"Erro interno: {str(e)}"}, status=500)

# projects/views.py

@login_required
def create_post_studio_view(request):
    """
    Renderiza a tela cheia de criação de posts (O Estúdio).
    """
    clients = Client.objects.all()
    connected_accounts = SocialAccount.objects.all()
    
    context = {
        'clients': clients,
        'connected_accounts': connected_accounts
    }
    return render(request, 'projects/create_post_studio.html', context)

@login_required
def get_clients_list_api(request):
    """
    Retorna uma lista simples de clientes (ID e Nome) para dropdowns.
    """
    clients = Client.objects.all().values('id', 'name')
    return JsonResponse({'clients': list(clients)})

@login_required
def meta_auth_start(request, client_id):
    """
    Inicia o fluxo de conexão para um Cliente específico.
    """
    # Guardamos o ID do cliente na sessão para saber a quem vincular depois
    request.session['meta_connect_client_id'] = client_id
    
    # Gera um token de estado aleatório para segurança
    state = secrets.token_urlsafe(16)
    request.session['meta_oauth_state'] = state
    
    service = MetaService()
    url = service.get_auth_url(state)
    
    return redirect(url)

@login_required
def meta_auth_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    print(f"--- CALLBACK INICIADO ---")
    
    if not state or state != request.session.get('meta_oauth_state'):
        messages.error(request, "Erro de Segurança: Estado inválido (CSRF).")
        return redirect('social_dashboard')
    
    client_id = request.session.get('meta_connect_client_id')
    client = get_object_or_404(Client, pk=client_id)
    
    # URL de retorno (deve ser idêntica à usada no início)
    current_domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    callback_url = f"{protocol}://{current_domain}/meta-callback/"

    # Troca o Code pelo Token
    service = MetaService()
    
    # Vamos fazer a troca manualmente aqui para pegar o erro se houver
    import requests
    token_url = (
        f"https://graph.facebook.com/v19.0/oauth/access_token?"
        f"client_id={settings.META_APP_ID}&"
        f"redirect_uri={callback_url}&"
        f"client_secret={settings.META_APP_SECRET}&"
        f"code={code}"
    )
    
    resp = requests.get(token_url)
    token_data = resp.json()
    
    print(f"Resposta do Token: {token_data}") # Olha o terminal!

    if 'access_token' in token_data:
        # Busca as páginas
        accounts = service.get_user_pages(token_data['access_token'], client)
        
        if not accounts:
            # SE ENTRAR AQUI, O FACEBOOK NÃO MANDOU NENHUMA PÁGINA
            messages.warning(request, "Conexão feita, mas NENHUMA página foi encontrada. Você marcou as páginas no popup?")
        else:
            messages.success(request, f"Sucesso! {len(accounts)} contas conectadas.")
            
        return redirect('social_dashboard')
    else:
        # Se der erro na troca do token
        error_msg = token_data.get('error', {}).get('message', 'Erro desconhecido')
        messages.error(request, f"Erro ao conectar Facebook: {error_msg}")
        return redirect('social_dashboard')

@login_required
def linkedin_auth_start(request, client_id):
    """ Inicia o login com LinkedIn """
    request.session['linkedin_client_id'] = client_id
    state = secrets.token_urlsafe(16)
    request.session['linkedin_oauth_state'] = state
    
    service = LinkedInService()
    url = service.get_auth_url(state)
    
    return redirect(url)

@login_required
def linkedin_auth_callback(request):
    """ Retorno do LinkedIn """
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')

    if error:
        messages.error(request, f"Usuário negou acesso ou erro LinkedIn: {error}")
        return redirect('social_dashboard')

    # Valida State (CSRF)
    saved_state = request.session.get('linkedin_oauth_state')
    if not state or state != saved_state:
        messages.error(request, "Estado inválido (Erro de segurança). Tente novamente.")
        return redirect('social_dashboard')

    # Recupera o Cliente
    client_id = request.session.get('linkedin_client_id')
    client = get_object_or_404(Client, pk=client_id)

    # Processa Token
    service = LinkedInService()
    token_data = service.exchange_code_for_token(code)

    if 'access_token' in token_data:
        account = service.save_account(token_data, client)
        if account:
            messages.success(request, f"LinkedIn conectado: {account.account_name}")
        else:
            messages.error(request, "Erro ao salvar dados do perfil.")
    else:
        messages.error(request, f"Erro ao obter token: {token_data.get('error_description')}")

    return redirect('social_dashboard')