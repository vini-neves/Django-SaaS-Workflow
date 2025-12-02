# projects/templatetags/project_extras.py

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Uso no template: {{ meu_dicionario|get_item:minha_chave }}
    """
    return dictionary.get(key)