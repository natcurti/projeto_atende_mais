from django.shortcuts import render

from contas.permissoes import somente_cliente, somente_equipe


@somente_cliente
def meus_tickets(request):
    """Meus tickets (RF07). Provisória: a lista completa chega no F2."""
    return render(request, "tickets/meus_tickets.html")


@somente_equipe
def fila(request):
    """Fila de atendimento (RF08). Provisória: a fila completa chega no F3."""
    return render(request, "tickets/fila.html")
