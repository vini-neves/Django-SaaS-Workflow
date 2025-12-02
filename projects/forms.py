# projects/forms.py
from django import forms
from .models import Client, Project
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

class ClientForm(forms.ModelForm):
    
    # Inputs de data para o navegador mostrar o calendário
    data_inicio_contrato = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}), 
        required=False
    )
    data_finalizacao_contrato = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}), 
        required=False
    )

    class Meta:
        model = Client
        # Lista de todos os campos que o formulário deve mostrar
        fields = [
            'name', 
            'cnpj', 
            'data_inicio_contrato', 
            'data_finalizacao_contrato',
            'nome_representante', 
            'celular_representante', 
            'email_representante',
            'anexo_contrato',
            'manual_marca'
        ]
        
        # Adiciona classes CSS e placeholders para os inputs
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nome Fantasia'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '00.000.000/0001-00'}),
            'nome_representante': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nome do Responsável'}),
            'celular_representante': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '(XX) 9XXXX-XXXX'}),
            'email_representante': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'contato@cliente.com'}),
            'anexo_contrato': forms.FileInput(attrs={'class': 'form-input'}),
            'manual_marca': forms.FileInput(attrs={'class': 'form-input'}),
        }



class TenantAuthenticationForm(AuthenticationForm):
    """
    Este formulário customizado faz a checagem do tenant.
    """
    def __init__(self, request=None, *args, **kwargs):
        """
        O 'request' é a chave. Ele nos diz qual tenant (agência)
        está sendo acessado.
        """
        self.request = request
        super().__init__(request=request, *args, **kwargs)

    def clean(self):
        # Roda a validação padrão primeiro (checa usuário e senha)
        # Isso nos dá o 'self.user_cache' (o usuário autenticado)
        super().clean() 

        if self.user_cache is None:
            # Se o login/senha falhou, não fazemos nada
            return

        # --- A VERIFICAÇÃO DE SEGURANÇA CRÍTICA ---
        # 'self.user_cache' é o usuário (ex: usuario_agencia)
        # 'self.request.tenant' é a agência da URL (ex: tenant2)

        # (Ignora a checagem para superusuários, se você quiser)
        if self.user_cache.is_superuser:
            return

        if self.user_cache.agency != self.request.tenant:
            # O usuário NÃO pertence a esta agência.
            # Rejeita o login.
            raise ValidationError(
                "Este usuário não pertence a esta agência. "
                "Verifique seu usuário e senha.",
                code='invalid_tenant'
            )

        return self.cleaned_data

class ProjectForm(forms.ModelForm):

    # Inputs de data para o navegador mostrar o calendário
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}), 
        required=False,
        label="Data de Início"
    )
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}), 
        required=False,
        label="Data de Entrega"
    )

    # Força o campo 'client' a ser um dropdown
    client = forms.ModelChoiceField(
        queryset=Client.objects.all(),
        widget=forms.Select(attrs={'class': 'form-input'}),
        label="Cliente"
    )

    class Meta:
        model = Project
        fields = ['name', 'client', 'start_date', 'due_date', 'description']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Campanha de Lançamento'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Breve descrição do projeto'}),
        }
        labels = {
            'name': 'Nome do Projeto',
            'description': 'Descrição (Opcional)',
        }

    def __init__(self, *args, **kwargs):
        # Pega o 'tenant' da view para filtrar o queryset de clientes
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

        if tenant:
            # Filtra o dropdown de Clientes para mostrar APENAS
            # os clientes da agência (tenant) atual.
            self.fields['client'].queryset = Client.objects.filter()