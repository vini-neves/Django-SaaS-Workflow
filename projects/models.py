from django.db import models
from django.conf import settings
import secrets
import os
import uuid
from django.utils.text import slugify

# --- ESCOLHAS GLOBAIS (STATUS) ---

KANBAN_TYPES = [
    ('general', 'Geral'),
    ('operational', 'Operacional'),
]

# Unificamos todos os status possíveis aqui
ALL_STATUS_CHOICES = [
    # --- Status Gerais ---
    ('todo', 'A Fazer'),
    ('doing', 'Em Andamento'),
    ('done', 'Concluído'),
    
    # --- Status Operacionais (Fluxo de Produção) ---
    ('briefing', 'Briefing'),
    ('copy', 'Copy'),
    ('design', 'Design'),
    ('internal_approval', 'Aprovação Interna'),
    ('client_approval', 'Aprovação Cliente'),
    ('scheduling', 'Agendamento'),
    ('published', 'Publicado'),
]

# --- 1. CLIENTE ---
class Client(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nome do Cliente")
    cnpj = models.CharField(max_length=18, verbose_name="CNPJ", blank=True, null=True)
    
    # Dados de Contrato
    data_inicio_contrato = models.DateField(verbose_name="Início do Contrato", blank=True, null=True)
    data_finalizacao_contrato = models.DateField(verbose_name="Fim do Contrato", blank=True, null=True)
    
    # Dados do Representante
    nome_representante = models.CharField(max_length=255, verbose_name="Nome do Representante", blank=True)
    celular_representante = models.CharField(max_length=20, verbose_name="Celular do Representante", blank=True)
    email_representante = models.EmailField(verbose_name="Email do Representante", blank=True)
    
    # Arquivos
    anexo_contrato = models.FileField(upload_to='contratos/', verbose_name="Anexo do Contrato", blank=True, null=True)
    manual_marca = models.FileField(upload_to='manual/', verbose_name="Anexo do Manual da Marca", blank=True, null=True)
    # Logo para o mockup de aprovação
    logo = models.ImageField(upload_to='logos_clientes/', verbose_name="Logo do Cliente", blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name="Cliente Ativo?")

    def __str__(self):
        return self.name


# --- 2. PROJETO ---
class Project(models.Model):
    STATUS_CHOICES = [
        ('em_andamento', 'Em Andamento'),
        ('finalizado', 'Finalizado'),
        ('pausado', 'Pausado'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="projects", null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name="Nome do Projeto")
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='em_andamento', verbose_name="Status")
    
    start_date = models.DateField(verbose_name="Data de Início", null=True, blank=True)
    due_date = models.DateField(verbose_name="Data de Entrega", null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# --- 3. REDES SOCIAIS (CONTAS) ---
class SocialAccount(models.Model):
    PLATFORM_CHOICES = [
        # Redes Sociais
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('tiktok', 'TikTok'),
        ('pinterest', 'Pinterest'),
        ('youtube', 'YouTube'),
        ('threads', 'Threads'),
        ('x', 'X (Twitter)'),
        
        # Ads / Tráfego Pago
        ('tiktok_ads', 'TikTok Ads'),
        ('linkedin_ads', 'LinkedIn Ads'),
        ('meta_ads', 'Meta Ads'),
        ('google_ads', 'Google Ads'),
        
        # Google Services
        ('google_my_business', 'Google Meu Negócio'),
        ('ga4', 'Google Analytics 4'),
    ]
    
    # ... (o restante da classe continua igual: client, platform, tokens, etc.) ...
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="social_accounts", null=True, blank=True, verbose_name="Cliente Vinculado")
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES) # Aumentei para 50 por segurança
    account_name = models.CharField(max_length=255, verbose_name="Nome da Conta")
    account_id = models.CharField(max_length=255, verbose_name="ID na Rede Social")
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    token_expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_platform_display()} - {self.account_name}"


# --- 4. POSTAGEM SOCIAL (CONTEÚDO & APROVAÇÃO) ---
class SocialPost(models.Model):
    # Conteúdo Base
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="social_posts")
    caption = models.TextField(verbose_name="Legenda/Copy", blank=True)
    media_file = models.FileField(upload_to='social_posts/', verbose_name="Imagem/Vídeo", blank=True, null=True)
    scheduled_for = models.DateTimeField(verbose_name="Agendamento", null=True, blank=True)
    
    # Destinos (M2M através de tabela intermediária)
    accounts = models.ManyToManyField(
        SocialAccount, 
        through='SocialPostDestination', 
        related_name="posts"
    )

    # Fluxo de Aprovação
    approval_status = models.CharField(
        max_length=30, 
        choices=[
            ('draft', 'Rascunho'), 
            ('copy_review', 'Aprovação: Copy'), 
            ('design_review', 'Aprovação: Design'), 
            ('internal_approval', 'Aprovação Interna'), 
            ('client_approval', 'Aprovação Cliente'), 
            ('approved_to_schedule', 'Pronto para Agendar')
        ],
        default='draft',
        verbose_name="Status de Aprovação"
    )
    
    # Link Seguro (Token)
    approval_token = models.CharField(max_length=64, unique=True, blank=True, null=True)
    
    # Feedback e Reprova
    feedback_text = models.TextField(blank=True, null=True, verbose_name="Motivo Reprova (Texto)")
    feedback_image_markup = models.TextField(blank=True, null=True, verbose_name="Rabisco na Imagem (Base64)")

    # Métricas
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Gera token automaticamente se não existir
        if not self.approval_token:
            self.approval_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Post - {self.client.name} ({self.get_approval_status_display()})"


# --- 5. DESTINOS DO POST (Intermediária) ---
class SocialPostDestination(models.Model):
    DESTINATION_CHOICES = [
        # Meta
        ('facebook_feed', 'Facebook - Feed'),
        ('facebook_story', 'Facebook - Story'),
        ('instagram_feed', 'Instagram - Feed'),
        ('instagram_story', 'Instagram - Story'),
        ('instagram_reel', 'Instagram - Reels'),
        ('threads_post', 'Threads'),
        
        # Vídeo
        ('youtube_video', 'YouTube - Vídeo Longo'),
        ('youtube_short', 'YouTube - Shorts'),
        ('tiktok_post', 'TikTok'),
        
        # Outros
        ('linkedin_feed', 'LinkedIn'),
        ('x_post', 'X (Twitter)'),
        ('pinterest_pin', 'Pinterest'),
    ]
    
    post = models.ForeignKey('SocialPost', on_delete=models.CASCADE)
    account = models.ForeignKey('SocialAccount', on_delete=models.CASCADE)
    format_type = models.CharField(max_length=50, choices=DESTINATION_CHOICES)
    
    def __str__(self):
        return f"{self.account} - {self.get_format_type_display()}"


# --- 6. TAREFA (KANBAN GERAL E OPERACIONAL) ---
class Task(models.Model):
    kanban_type = models.CharField(max_length=20, choices=KANBAN_TYPES, default='general')
    status = models.CharField(max_length=50, choices=ALL_STATUS_CHOICES, default='todo')
    
    social_post = models.ForeignKey('SocialPost', on_delete=models.SET_NULL, null=True, blank=True, related_name='task_link')
    
    # CORREÇÃO 1: Permite tarefas sem projeto (obrigatório para posts avulsos)
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='tasks',
        null=True,  # <--- ESSENCIAL
        blank=True  # <--- ESSENCIAL
    )

    PRIORITY_CHOICES = [
        ('high', 'Alta'),
        ('medium', 'Média'),
        ('low', 'Baixa'),
    ]
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='low' # Importante ter um default para tarefas antigas
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # CAMPOS DE DATA E ORDENAÇÃO
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    order = models.IntegerField(default=0) 
    
    # CAMPOS DE USUÁRIO
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="assigned_tasks",
        verbose_name="Atribuído a"
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title
        
    def to_dict(self):
        """ Retorna dados para o Frontend (JSON) """
        
        project_name = "Sem Projeto"
        initials = '--'
        
        if self.assigned_to:
            # 1. Pega os campos diretamente, garantindo que não seja None
            first = (self.assigned_to.first_name or "").strip()
            last = (self.assigned_to.last_name or "").strip()
            
            # 2. Se tiver os dois nomes, pega a 1ª letra de cada
            if first and last:
                initials = f"{first[0]}{last[0]}"
            
            # 3. Se só tiver o primeiro nome (mas composto), tenta pegar do split
            elif first:
                names = first.split()
                if len(names) >= 2:
                     initials = f"{names[0][0]}{names[-1][0]}"
                else:
                    initials = first[:2]
            
            # 4. Fallback: Se não tiver nome nenhum, usa o username
            else:
                initials = self.assigned_to.username[:2]

        if self.project:
            project_name = self.project.name
        elif self.social_post and self.social_post.client:
            # Se não tem projeto, mas tem post, usa o nome do cliente
            project_name = f"Cliente: {self.social_post.client.name}"

        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or "Nenhuma descrição.",
            'status': self.status,
            'priority': self.priority,
            'status_display': self.get_status_display(),    
            'project_name': project_name,
            'order': self.order,
            'created_at': self.created_at.strftime('%d/%m/%Y'),
            'updated_at': self.updated_at.strftime('%d/%m/%Y') if self.updated_at else "", 
            'assigned_to_username': self.assigned_to.username if self.assigned_to else None,
            'assigned_to_initials': self.assigned_to.username[0].upper() if self.assigned_to and self.assigned_to.username else '?',
            'social_post_id': self.social_post.id if self.social_post else None,
            'assigned_to_initials': initials.upper(),
        }

# --- 7. EVENTOS DO CALENDÁRIO (SIMPLES) ---
class CalendarEvent(models.Model):
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('linkedin', 'LinkedIn'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
    ]

    TYPE_CHOICES = [
        ('Feed', 'Feed'),
        ('Story', 'Story'),
        ('Reels', 'Reels'),
    ]

    STATUS_CHOICES = [
        ('Draft', 'Rascunho'),
        ('Pending', 'Pendente Aprovação'),
        ('Scheduled', 'Agendado'),
        ('Published', 'Publicado'),
    ]

    # Conexão real com o Cliente
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    
    title = models.CharField(max_length=200, blank=True) # Título pode ser vazio se tiver cliente
    date = models.DateField()
    time = models.TimeField(default="09:00")
    
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='instagram')
    post_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='Feed')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    
    # Novos campos para o Modal Completo
    caption = models.TextField(blank=True, null=True)
    media = models.ImageField(upload_to='posts_media/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.name} - {self.date}"

def client_r2_path(instance, filename):
    
    # Opção B: Se você usa django-tenants e quer o nome do tenant atual:
    from django.db import connection
    agency_name = slugify(connection.tenant.name)

    # 2. Pega o nome do Cliente e limpa (tira espaços e acentos)
    # Ex: "McDonald's Brasil" vira "mcdonalds-brasil"
    client_name = slugify(instance.folder.client.name)
    
    # 3. Pega o nome da Pasta
    folder_name = slugify(instance.folder.name) if instance.folder else 'root'
    
    # 4. Mantém a extensão original do arquivo
    name, ext = os.path.splitext(filename)
    clean_filename = slugify(name) + ext
    unique_suffix = str(uuid.uuid4())[:4]
    final_filename = f"{clean_filename}_{unique_suffix}{ext}"

    return f'{agency_name}/{client_name}/{folder_name}/{final_filename}'

class MediaFolder(models.Model):
    name = models.CharField("Nome da Pasta", max_length=255)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='folders')
    
    # Auto-relacionamento: Permite criar subpastas dentro de pastas
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        # Evita criar duas pastas com mesmo nome no mesmo lugar
        unique_together = ['parent', 'name', 'client'] 

    def __str__(self):
        return self.name

class MediaFile(models.Model):
    folder = models.ForeignKey(MediaFolder, on_delete=models.CASCADE, related_name='files')
    # O upload_to chama a função acima para decidir o caminho no R2
    file = models.FileField(upload_to=client_r2_path) 
    filename = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Salva metadados automaticamente antes de enviar
        if self.file:
            self.filename = os.path.basename(self.file.name)
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self):
        return self.filename