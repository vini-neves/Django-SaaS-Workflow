from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class Client(TenantMixin):
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

class Domain(DomainMixin):
    pass