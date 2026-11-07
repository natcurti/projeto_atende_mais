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


@register.filter
def estrelas(nota):
    """Nota de 1 a 5 como estrelas: 4 vira "★★★★☆"."""
    try:
        nota = int(nota)
    except (TypeError, ValueError):
        return ""
    return "★" * nota + "☆" * (5 - nota)


@register.filter
def duracao(horas):
    """Duração em horas, legível: 0,75 vira "45 min"; 18,5 vira "18,5 h"; 55 vira "2,3 dias"."""
    from django.utils.formats import number_format

    if horas is None:
        return "—"
    if horas < 1:
        return f"{round(horas * 60)} min"
    if horas < 48:
        return f"{number_format(horas, 1)} h"
    return f"{number_format(horas / 24, 1)} dias"
