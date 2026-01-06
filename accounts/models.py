# accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django_tenants.models import TenantMixin, DomainMixin
from django.conf import settings

# 1. Modelo da Agência (Tenant)
class Agency(TenantMixin):
    name = models.CharField(max_length=255, verbose_name="Nome da Agência")
    created_on = models.DateField(auto_now_add=True)

    # Customização White-Label
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    primary_color = models.CharField(max_length=7, default='#FFFFFF', verbose_name="Cor Primária")
    secondary_color = models.CharField(max_length=7, default='#000000', verbose_name="Cor Secundária")

    auto_create_schema = True

    def __str__(self):
        return self.name

class Domain(DomainMixin):
    pass

# 2. Modelo de Usuário Customizado (Atualizado)
class CustomUser(AbstractUser):
    ROLES = (
        ('admin', 'Administrador'),
        ('editor', 'Editor'),
        ('viewer', 'Visualizador'),
    )

    # Link com a Agência
    agency = models.ForeignKey(
        Agency, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name="users"
    )
    
    # --- NOVOS CAMPOS ADICIONADOS ---
    role = models.CharField(max_length=20, choices=ROLES, default='viewer', verbose_name="Função")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    def __str__(self):
        return self.username

class GoogleApiCredentials(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name="google_credentials"
    )
    refresh_token = models.TextField(verbose_name="Refresh Token")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Credenciais do Google para {self.user.username}"