# accounts/views.py

from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from google_auth_oauthlib.flow import Flow # A biblioteca que instalamos
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from .models import GoogleApiCredentials
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from .models import Agency

# Esta view é acessada pelo usuário para INICIAR o login
def get_google_client_config():
    return {
        "web": {
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "redirect_uris": [settings.GOOGLE_OAUTH_REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


@login_required
def google_auth_start(request):
    """
    Inicia o fluxo OAuth 2.0.
    """
    client_config = get_google_client_config()

    # --- CORREÇÃO AQUI ---
    # Trocamos 'from_client_secrets_file' por 'from_client_config'
    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=settings.GOOGLE_OAUTH_SCOPES,
        redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI
    )
    # --- FIM DA CORREÇÃO ---

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent' 
    )
    
    request.session['oauth_state'] = state
    
    return redirect(authorization_url)


@login_required
def google_auth_callback(request):
    """
    O Google redireciona para cá após o usuário dar permissão.
    """
    state = request.session.pop('oauth_state', None)
    if state is None or state != request.GET.get('state'):
        return HttpResponseBadRequest("Falha na verificação de estado (CSRF).")

    client_config = get_google_client_config()
    
    # --- CORREÇÃO AQUI ---
    # Trocamos 'from_client_secrets_file' por 'from_client_config'
    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=settings.GOOGLE_OAUTH_SCOPES,
        redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI
    )
    # --- FIM DA CORREÇÃO ---

    code = request.GET.get('code')
    
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Deleta credenciais antigas se existirem
        GoogleApiCredentials.objects.filter(user=request.user).delete()
        
        # Salva o novo refresh token
        GoogleApiCredentials.objects.create(
            user=request.user,
            refresh_token=credentials.refresh_token
        )

        # Redireciona de volta para o calendário do tenant
        # (Você pode mudar isso para uma página de "Sucesso" no admin público)
        return redirect('http://tenant1.localhost:8000/calendar/')

    except Exception as e:
        return HttpResponseBadRequest(f"Erro ao obter token: {e}")


User = get_user_model()

@login_required
def user_management_view(request):
    """Lista usuários baseado na permissão (Superuser vê tudo, Admin vê sua agência)."""
    
    if request.user.is_superuser:
        # Vê todos os usuários e todas as agências
        users = User.objects.all().select_related('agency').order_by('-date_joined')
        agencies = Agency.objects.all()
    else:
        # Vê apenas usuários da sua própria agência
        # Nota: Se o usuário não tiver agência vinculada, retorna lista vazia para evitar erro
        user_agency = request.user.agency
        if user_agency:
            users = User.objects.filter(agency=user_agency).order_by('-date_joined')
            agencies = Agency.objects.filter(id=user_agency.id)
        else:
            users = User.objects.none()
            agencies = Agency.objects.none()
        
    context = {
        'users': users,
        'agencies': agencies,
        'is_superuser': request.user.is_superuser
    }
    return render(request, 'accounts/user_list.html', context)

User = get_user_model()

@login_required
@require_POST
def create_user_api(request):
    """API para criar ou editar usuários."""
    try:
        data = request.POST
        user_id = data.get('user_id') # Pega o ID oculto do HTML
        password = data.get('password')
        username = data.get('username')
        is_active_status = 'is_active' in data
        
        # 1. Determina a Agência (Lógica comum para Create e Update)
        agency = None
        if request.user.is_superuser:
            agency_id = data.get('agency')
            if agency_id:
                try:
                    agency = Agency.objects.get(id=agency_id)
                except Agency.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Agência inválida.'}, status=400)
        else:
            agency = request.user.agency

        # =================================================
        # MODO EDIÇÃO (Se tem user_id)
        # =================================================
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Usuário não encontrado.'}, status=404)

            # Validação: Username já existe? (Excluindo o próprio usuário da busca)
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                return JsonResponse({'status': 'error', 'message': 'Este nome de usuário já está em uso por outra pessoa.'}, status=400)

            # Atualiza campos básicos
            user.first_name = data.get('first_name')
            user.last_name = data.get('last_name')
            user.email = data.get('email')
            user.username = username
            user.role = data.get('role', 'viewer')
            user.is_active = is_active_status
            
            # Só atualiza a agência se for superuser ou lógica específica
            if agency: 
                user.agency = agency

            # Atualiza senha APENAS se foi fornecida
            if password:
                if len(password) < 8:
                    return JsonResponse({'status': 'error', 'message': 'A nova senha deve ter no mínimo 8 caracteres.'}, status=400)
                user.set_password(password) # Criptografa a nova senha
            
            user.save()
            return JsonResponse({'status': 'success', 'message': 'Usuário atualizado com sucesso!'})

        # =================================================
        # MODO CRIAÇÃO (Se NÃO tem user_id)
        # =================================================
        else:
            # Validação: Senha é obrigatória na criação
            if not password or len(password) < 8:
                return JsonResponse({'status': 'error', 'message': 'A senha deve ter no mínimo 8 caracteres.'}, status=400)
            
            # Validação: Username já existe?
            if User.objects.filter(username=username).exists():
                 return JsonResponse({'status': 'error', 'message': 'Nome de usuário já existe.'}, status=400)

            # Criação
            new_user = User.objects.create_user(
                username=username,
                email=data.get('email'),
                password=password,
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                role=data.get('role', 'viewer'),
                agency=agency
            )
            
            new_user.is_active = is_active_status
            new_user.save()

            return JsonResponse({'status': 'success', 'message': 'Usuário criado com sucesso!'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)