from django.contrib.auth import get_user_model
from django.shortcuts import render

from .models import Categoria, Ticket


def inicio(request):
    """Página inicial provisória: mostra que o sistema e o banco estão funcionando."""
    contexto = {
        "tickets": Ticket.objects.select_related("cliente").order_by("-id")[:5],
        "total_tickets": Ticket.objects.count(),
        "total_usuarios": get_user_model().objects.count(),
        "total_categorias": Categoria.objects.count(),
    }
    return render(request, "inicio.html", contexto)
