from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import models # Para usar models.Max
from django.urls import reverse
import json
import datetime
from django.utils import timezone
import secrets
from django.contrib.auth import views as auth_views
from .models import Task, CalendarEvent, Project, Client, SocialPost, SocialAccount
from .forms import ClientForm, TenantAuthenticationForm, ProjectForm
from accounts.models import CustomUser

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
    # Define as colunas baseadas no tipo
    if kanban_type == 'operational':
        stages = [
            ('briefing', 'Briefing'),
            ('copy', 'Copy'),
            ('design', 'Design'),
            ('internal_approval', 'Aprovação Interna'),
            ('client_approval', 'Aprovação Cliente'),
            ('scheduling', 'Agendamento'),
        ]
        template = 'projects/operational_kanban.html'
    else:
        stages = [('todo', 'A Fazer'), ('doing', 'Em Andamento'), ('done', 'Concluído')]
        template = 'projects/general_kanban.html'

    # Busca tarefas APENAS desse tipo
    tasks = Task.objects.filter(kanban_type=kanban_type).order_by('order')
    
    # Organiza para o template
    kanban_data = {}
    for key, label in stages:
        kanban_data[key] = tasks.filter(status=key)

    context = {
        'stages': stages,
        'kanban_data': kanban_data,
        'kanban_type': kanban_type
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
    Painel principal de gestão de redes sociais.
    """
    # Busca as contas conectadas
    connected_accounts = SocialAccount.objects.all()
    clients = Client.objects.all()
    
    # Pega a hora atual para saber o que é passado e futuro
    now = timezone.now()
    
    # CORREÇÃO: Usamos 'approval_status' e data para filtrar
    
    # 1. Posts Agendados (Aprovados e Data no Futuro)
    scheduled_posts = SocialPost.objects.filter(
        approval_status='approved_to_schedule',
        scheduled_for__gte=now
    ).order_by('scheduled_for')
    
    # 2. Posts Publicados (Aprovados e Data no Passado)
    published_posts = SocialPost.objects.filter(
        approval_status='approved_to_schedule',
        scheduled_for__lt=now
    ).order_by('-scheduled_for')
    
    context = {
        'connected_accounts': connected_accounts,
        'scheduled_posts': scheduled_posts,
        'published_posts': published_posts,
        'clients': clients,
    }
    return render(request, 'projects/social_dashboard.html', context)
pass
    

@method_decorator(csrf_exempt, name='dispatch')
class CreateSocialPostAPI(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        try:
            
            data = request.POST
            content = data.get('content')
            scheduled_at_str = data.get('scheduled_for')
            account_ids = data.getlist('accounts')
            image_file = request.FILES.get('image')
            client_id = data.get('client')
            
            if not content or not scheduled_at_str or not account_ids or not client_id:
                 return JsonResponse({'status': 'error', 'message': 'Campos obrigatórios faltando.'}, status=400)

            client = get_object_or_404(Client, pk=client_id)
            
            try:
                scheduled_for = datetime.datetime.strptime(scheduled_at_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Data inválida.'}, status=400)
            # O status inicial é 'scheduled' (agendado)
            post = SocialPost.objects.create(
                content=content,
                scheduled_for=scheduled_for,
                image=image_file,
                approval_status='draft',
                created_by=request.user,
                client=client
            )

            if account_ids:
                accounts = SocialAccount.objects.filter(id__in=account_ids)
                from .models import SocialPostDestination
                for acc in accounts:
                    # Tenta adivinhar o formato baseado na plataforma
                    fmt = 'feed'
                    if acc.platform in ['instagram', 'tiktok', 'youtube']:
                        # Lógica simples: se for tiktok é vertical, etc.
                        # (Podemos melhorar isso depois)
                        pass 
                    
                    SocialPostDestination.objects.create(
                        post=post, 
                        account=acc, 
                        format_type=fmt
                    )

                # 3. CRIAÇÃO AUTOMÁTICA DA TAREFA NO KANBAN OPERACIONAL
                # Calcula a ordem
                max_order = Task.objects.filter(
                    kanban_type='operational', 
                    status='briefing'
                ).aggregate(models.Max('order'))['order__max']
                new_order = (max_order if max_order is not None else -1) + 1

                Task.objects.create(
                    kanban_type='operational',
                    status='briefing', # Entra na primeira coluna do fluxo
                    title=f"Post: {client.name} - {scheduled_for.strftime('%d/%m')}", # Título automático
                    description=content[:100], # Usa o começo do post como descrição
                    social_post=post, # VINCULA AO POST
                    project=None, # (Opcional: se o cliente tiver um projeto padrão, poderia vincular)
                    created_by=request.user,
                    order=new_order
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'Post criado e tarefa enviada para o Kanban!',
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
    """
    Cria uma tarefa operacional (Briefing) e o objeto SocialPost associado.
    Aceita uploads de arquivos (imagem de referência).
    """
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        try:
            # Como o form tem enctype="multipart/form-data", usamos request.POST e request.FILES
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            project_id = request.POST.get('project')
            assigned_to_id = request.POST.get('assigned_to')
            
            # Pega o arquivo de referência (se houver)
            reference_image = request.FILES.get('reference_image')

            # Validação Básica
            if not title or not project_id:
                return JsonResponse({'status': 'error', 'message': 'Título e Projeto são obrigatórios.'}, status=400)

            # Busca o Projeto e o Cliente
            project = get_object_or_404(Project, id=project_id)
            if not project.client:
                return JsonResponse({'status': 'error', 'message': 'Este projeto não tem um cliente vinculado.'}, status=400)

            # 1. CRIAR O SOCIAL POST (O "Conteúdo")
            # Ele nasce ligado ao Cliente do projeto.
            # A imagem de referência vai para o 'media_file' por enquanto.
            social_post = SocialPost.objects.create(
                client=project.client,
                caption=description, # Usamos o briefing como legenda inicial
                media_file=reference_image, 
                created_by=request.user,
                approval_status='draft' # Status interno do post
            )

            # 2. CALCULAR A ORDEM NO KANBAN
            # Busca a maior ordem na coluna 'briefing' do tipo 'operational'
            max_order = Task.objects.filter(
                kanban_type='operational', 
                status='briefing'
            ).aggregate(models.Max('order'))['order__max']
            
            new_order = (max_order if max_order is not None else -1) + 1

            # 3. CRIAR A TAREFA (O "Card" do Kanban)
            task = Task.objects.create(
                kanban_type='operational',
                status='briefing', # Começa sempre na primeira coluna
                project=project,
                social_post=social_post, # LIGAÇÃO CRUCIAL: Tarefa -> Post
                title=title,
                description=description,
                order=new_order,
                created_by=request.user,
                assigned_to_id=assigned_to_id if assigned_to_id else None
            )

            # 4. RETORNO PARA O JAVASCRIPT
            return JsonResponse({
                'status': 'success',
                'message': 'Demanda iniciada com sucesso!',
                'task': task.to_dict() # Retorna os dados para desenhar o card na hora
            }, status=201)

        except Exception as e:
            # Log do erro para debug (opcional: print(e))
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