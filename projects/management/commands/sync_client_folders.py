import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from projects.models import Client, MediaFolder, MediaFile

class Command(BaseCommand):
    help = 'Cria pastas padrão para todos os clientes existentes e sincroniza com R2'

    def handle(self, *args, **kwargs):
        clients = Client.objects.all()
        
        self.stdout.write(f"Encontrados {clients.count()} clientes. Iniciando sincronização...")

        # Defina aqui as pastas padrão que todo cliente deve ter
        DEFAULT_FOLDERS = ['Geral', 'Briefing', 'Entregas', 'Fotos Brutas']

        for client in clients:
            self.stdout.write(f"Processando: {client.name}...")
            
            for folder_name in DEFAULT_FOLDERS:
                # 1. Cria a pasta no Banco de Dados (se não existir)
                folder_obj, created = MediaFolder.objects.get_or_create(
                    name=folder_name,
                    client=client,
                    parent=None # Raiz do cliente
                )

                if created:
                    self.stdout.write(f"  > Pasta '{folder_name}' criada no Banco.")
                    
                    # 2. (Opcional) Força a criação no Cloudflare R2
                    # O R2/S3 não tem "pastas vazias", então criamos um arquivo oculto .keep
                    # para garantir que a estrutura de diretórios exista visualmente em alguns clients S3.
                    try:
                        dummy_file = ContentFile(b"", name=".keep")
                        
                        # Cria um arquivo "fantasma" para marcar o território no R2
                        MediaFile.objects.create(
                            folder=folder_obj,
                            file=dummy_file,
                            filename=".keep",
                            file_size=0
                        )
                        self.stdout.write(f"  > Pasta '{folder_name}' sincronizada no R2.")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  ! Erro ao sync R2: {e}"))

        self.stdout.write(self.style.SUCCESS('Sincronização concluída com sucesso!'))