# projects/services.py
import requests
from django.conf import settings
from .models import SocialAccount
import urllib.parse

class MetaService:
    BASE_URL = "https://graph.facebook.com/v19.0"

    def get_auth_url(self, state_token):
        """ Gera a URL para o botão 'Conectar Facebook' """
        scopes = ",".join(settings.META_SCOPES)
        return (
            f"https://www.facebook.com/v19.0/dialog/oauth?"
            f"client_id={settings.META_APP_ID}&"
            f"redirect_uri={settings.META_REDIRECT_URI}&"
            f"state={state_token}&"
            f"scope={scopes}"
        )

    def exchange_code_for_token(self, code):
        """ Troca o código temporário por um User Access Token """
        url = (
            f"{self.BASE_URL}/oauth/access_token?"
            f"client_id={settings.META_APP_ID}&"
            f"redirect_uri={settings.META_REDIRECT_URI}&"
            f"client_secret={settings.META_APP_SECRET}&"
            f"code={code}"
        )
        response = requests.get(url)
        return response.json() # Retorna {access_token, ...}

    def get_user_pages(self, user_access_token, client_obj):
        """
        Busca as Páginas do Facebook e Contas do Instagram vinculadas.
        """
        print(f"--- DEBUG META START ---")
        print(f"1. Token Recebido: {user_access_token[:10]}...") # Mostra só o começo por segurança
        
        # 1. Busca as páginas que o usuário administra
        url = f"{self.BASE_URL}/me/accounts?access_token={user_access_token}&fields=id,name,access_token,instagram_business_account"
        
        response = requests.get(url)
        data = response.json()

        # ESPIONAGEM AQUI
        print(f"2. Resposta Bruta do Facebook: {data}")

        if 'data' not in data:
            print("ERRO CRÍTICO: Campo 'data' não encontrado na resposta.")
            return []
        
        if len(data['data']) == 0:
            print("ALERTA: O Facebook retornou uma lista de páginas VAZIA. O usuário tem páginas criadas?")

        saved_accounts = []

        for page in data['data']:
            print(f"3. Processando Página: {page.get('name')} (ID: {page.get('id')})")
            
            try:
                # --- SALVAR PÁGINA DO FACEBOOK ---
                fb_account, created = SocialAccount.objects.update_or_create(
                    account_id=page['id'],
                    client=client_obj,
                    defaults={
                        'platform': 'facebook',
                        'account_name': page['name'],
                        'access_token': page['access_token'],
                        'is_active': True
                    }
                )
                print(f"   -> Facebook Salvo? {created} (ID BD: {fb_account.id})")
                saved_accounts.append(fb_account)

                # --- SALVAR CONTA DO INSTAGRAM (Se houver) ---
                if 'instagram_business_account' in page:
                    ig_data = page['instagram_business_account']
                    print(f"   -> Instagram Encontrado: {ig_data}")
                    
                    ig_info = self.get_instagram_details(ig_data['id'], user_access_token)
                    
                    ig_account, created = SocialAccount.objects.update_or_create(
                        account_id=ig_data['id'],
                        client=client_obj,
                        defaults={
                            'platform': 'instagram',
                            'account_name': ig_info.get('username', 'Instagram User'),
                            'access_token': page['access_token'], 
                            'is_active': True
                        }
                    )
                    print(f"   -> Instagram Salvo? {created}")
                    saved_accounts.append(ig_account)
                else:
                    print("   -> Nenhuma conta de Instagram vinculada a esta página.")

            except Exception as e:
                print(f"ERRO AO SALVAR NO BANCO: {e}")

        print(f"--- DEBUG META END ---")
        return saved_accounts
        
    def get_instagram_details(self, ig_id, access_token):
        """ Busca detalhes (username) da conta do Instagram """
        url = f"{self.BASE_URL}/{ig_id}?fields=username,profile_picture_url&access_token={access_token}"
        response = requests.get(url)
        return response.json()# projects/services.py
import requests
from django.conf import settings
from .models import SocialAccount

class MetaService:
    BASE_URL = "https://graph.facebook.com/v19.0"

    def get_auth_url(self, state_token):
        """ Gera a URL para o botão 'Conectar Facebook' """
        scopes = ",".join(settings.META_SCOPES)
        return (
            f"https://www.facebook.com/v19.0/dialog/oauth?"
            f"client_id={settings.META_APP_ID}&"
            f"redirect_uri={settings.META_REDIRECT_URI}&"
            f"state={state_token}&"
            f"scope={scopes}"
        )

    def exchange_code_for_token(self, code):
        """ Troca o código temporário por um User Access Token """
        url = (
            f"{self.BASE_URL}/oauth/access_token?"
            f"client_id={settings.META_APP_ID}&"
            f"redirect_uri={settings.META_REDIRECT_URI}&"
            f"client_secret={settings.META_APP_SECRET}&"
            f"code={code}"
        )
        response = requests.get(url)
        return response.json() # Retorna {access_token, ...}

    def get_user_pages(self, user_access_token, client_obj):
        """
        Busca as Páginas do Facebook e Contas do Instagram vinculadas.
        Salva ou atualiza no banco de dados.
        """
        # 1. Busca as páginas que o usuário administra
        url = f"{self.BASE_URL}/me/accounts?access_token={user_access_token}&fields=id,name,access_token,instagram_business_account"
        
        response = requests.get(url)
        data = response.json()

        if 'data' not in data:
            print("Erro ao buscar páginas:", data)
            return []

        saved_accounts = []

        for page in data['data']:
            # --- SALVAR PÁGINA DO FACEBOOK ---
            # O token da página (page_access_token) é vital para postar sem o usuário estar logado
            fb_account, created = SocialAccount.objects.update_or_create(
                account_id=page['id'],
                client=client_obj, # Vincula ao cliente da agência
                defaults={
                    'platform': 'facebook',
                    'account_name': page['name'],
                    'access_token': page['access_token'], # Token específico da página
                    'is_active': True
                }
            )
            saved_accounts.append(fb_account)

            # --- SALVAR CONTA DO INSTAGRAM (Se houver) ---
            if 'instagram_business_account' in page:
                ig_data = page['instagram_business_account']
                # Precisamos buscar o nome do Instagram (a lista de pages só dá o ID)
                ig_info = self.get_instagram_details(ig_data['id'], user_access_token)
                
                ig_account, created = SocialAccount.objects.update_or_create(
                    account_id=ig_data['id'],
                    client=client_obj,
                    defaults={
                        'platform': 'instagram',
                        'account_name': ig_info.get('username', 'Instagram User'),
                        # Instagram usa o token do usuário ou da página vinculada
                        'access_token': page['access_token'], 
                        'is_active': True
                    }
                )
                saved_accounts.append(ig_account)
        
        return saved_accounts

    def get_instagram_details(self, ig_id, access_token):
        """ Busca detalhes (username) da conta do Instagram """
        url = f"{self.BASE_URL}/{ig_id}?fields=username,profile_picture_url&access_token={access_token}"
        response = requests.get(url)
        return response.json()


class LinkedInService:
    # URLs Oficiais
    AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    USER_INFO_URL = "https://api.linkedin.com/v2/userinfo"

    def get_auth_url(self, state_token):
        """ Gera a URL do botão 'Conectar LinkedIn' """
        scope_string = " ".join(settings.LINKEDIN_SCOPES) # LinkedIn usa espaço, não vírgula
        return (
            f"{self.AUTH_URL}?"
            f"response_type=code&"
            f"client_id={settings.LINKEDIN_CLIENT_ID}&"
            f"redirect_uri={settings.LINKEDIN_REDIRECT_URI}&"
            f"state={state_token}&"
            f"scope={scope_string}"
        )

    def exchange_code_for_token(self, code):
        """ Troca o código pelo Access Token """
        payload = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.LINKEDIN_REDIRECT_URI,
            'client_id': settings.LINKEDIN_CLIENT_ID,
            'client_secret': settings.LINKEDIN_CLIENT_SECRET
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        response = requests.post(self.TOKEN_URL, data=payload, headers=headers)
        return response.json()

    def get_user_profile(self, access_token):
        """ Busca dados do usuário (Nome, Foto, Sub/ID) """
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(self.USER_INFO_URL, headers=headers)
        return response.json()

    def save_account(self, token_data, client_obj):
        """ Salva a conta no banco """
        access_token = token_data.get('access_token')
        if not access_token:
            return None

        # Busca dados do perfil
        profile_data = self.get_user_profile(access_token)
        
        # O ID único no OpenID Connect chama-se 'sub'
        linkedin_id = profile_data.get('sub')
        name = profile_data.get('name')
        picture = profile_data.get('picture', '')

        if not linkedin_id:
            return None

        # Salva no banco (Tabela SocialAccount)
        account, created = SocialAccount.objects.update_or_create(
            account_id=linkedin_id,
            client=client_obj,
            defaults={
                'platform': 'linkedin',
                'account_name': name,
                'access_token': access_token,
                # O token do LinkedIn dura 60 dias, depois precisa renovar
                'is_active': True 
            }
        )
        return account

class TikTokService:
    # Endpoints da API V2 do TikTok
    AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
    TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
    USER_INFO_URL = "https://open.tiktokapis.com/v2/user/info/"
    
    def get_auth_url(self, state_token):
        """
        Gera a URL para o usuário clicar e autorizar o app.
        """
        # Escopos necessários para ler perfil e postar vídeos
        scopes = [
            "user.info.basic",
            # "video.upload",
            # "video.publish"
        ]
        
        # AQUI ESTÁ A CORREÇÃO (client_key em vez de client_id)
        params = {
            "client_key": settings.TIKTOK_CLIENT_KEY, 
            "response_type": "code",
            "scope": ",".join(scopes), # Separa os escopos por vírgula
            "redirect_uri": settings.TIKTOK_REDIRECT_URI,
            "state": state_token,
        }
        
        # Converte o dicionário para formato de URL (ex: key=valor&key2=valor2)
        url_params = urllib.parse.urlencode(params)
        
        return f"{self.AUTH_URL}?{url_params}"

    def get_access_token(self, code):
        """
        Troca o 'code' recebido no callback pelo 'access_token' definitivo.
        """
        data = {
            "client_key": settings.TIKTOK_CLIENT_KEY,
            "client_secret": settings.TIKTOK_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.TIKTOK_REDIRECT_URI,
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache"
        }

        try:
            response = requests.post(self.TOKEN_URL, data=data, headers=headers)
            response.raise_for_status() # Levanta erro se não for 200 OK
            return response.json() # Retorna o JSON com access_token e open_id
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao obter token do TikTok: {e}")
            if response is not None:
                print(f"Detalhes do erro: {response.text}")
            return None

    def get_user_info(self, access_token):
        """
        (Opcional) Busca nome e foto do usuário para salvar no banco.
        """
        fields = ["display_name", "avatar_url"]
        
        params = {
            "fields": ",".join(fields)
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        try:
            response = requests.get(self.USER_INFO_URL, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json().get('data', {})
                return {
                    'name': data.get('display_name', 'Usuário TikTok'),
                    'avatar': data.get('avatar_url', '')
                }
            return None
        except Exception as e:
            print(f"Erro ao buscar info do usuário: {e}")
            return None