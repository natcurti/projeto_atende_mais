"""Filtros de template do atende+. Uso: {% load atende %}"""

from django import template
from django.utils.timesince import timesince

register = template.Library()


@register.filter
def tempo_curto(data):
    """Tempo desde `data` só com a maior unidade: "2 horas" em vez de "2 horas, 5 minutos"."""
    if not data:
        return ""
    return timesince(data, depth=1)
