# projects/admin.py

from django.contrib import admin
from .models import Project, Task, Client, CalendarEvent, SocialAccount, SocialPost, SocialPostDestination

# --- ADMIN INLINE ---
class SocialPostDestinationInline(admin.TabularInline):
    model = SocialPostDestination
    extra = 1

# --- ADMIN CLASSES ---

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'cnpj', 'nome_representante', 'data_inicio_contrato')
    search_fields = ('name', 'cnpj', 'email_representante')
    list_filter = ('data_inicio_contrato',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'status', 'start_date', 'due_date', 'created_at')
    search_fields = ('name',)
    list_filter = ('status', 'client')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    # 'updated_at' agora existe, então podemos usá-lo
    list_display = ('title', 'project', 'status', 'kanban_type', 'assigned_to', 'updated_at')
    list_filter = ('status', 'kanban_type', 'assigned_to', 'project')
    search_fields = ('title', 'description')
    list_display_links = ('title', 'project')

class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'date', 'platform', 'status', 'post_type')
    list_filter = ('status', 'platform', 'post_type', 'date')
    search_fields = ('title', 'client__name', 'caption')
    date_hierarchy = 'date'

@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'platform', 'client', 'is_active', 'token_expires_at')
    list_filter = ('platform', 'is_active', 'client')
    search_fields = ('account_name', 'account_id')

@admin.register(SocialPost)
class SocialPostAdmin(admin.ModelAdmin):
    # CORREÇÃO: Usamos 'caption' em vez de 'content' e 'approval_status' em vez de 'status'
    list_display = ('caption', 'client', 'approval_status', 'scheduled_for')
    list_filter = ('approval_status', 'client')
    search_fields = ('caption',)
    inlines = [SocialPostDestinationInline]

@admin.register(SocialPostDestination)
class SocialPostDestinationAdmin(admin.ModelAdmin):
    # CORREÇÃO: Usamos 'format_type' em vez de 'platform_type'
    list_display = ('post', 'account', 'format_type')
    list_filter = ('format_type', 'account')