from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from contas.permissoes import somente_cliente, somente_equipe

from . import services
from .forms import FiltroFilaForm, GerenciarTicketForm, NovoTicketForm, RespostaForm
from .models import Ticket


# ---------- Cliente ----------

@somente_cliente
def meus_tickets(request):
    """Meus tickets (RF07): só os tickets do cliente logado (RN08), com filtro por situação."""
    tickets = (
        Ticket.objects.filter(cliente=request.user)
        .select_related("categoria")
        .order_by("-atualizado_em")
    )
    situacao = request.GET.get("situacao", "")
    if situacao in Ticket.Situacao.values:
        tickets = tickets.filter(situacao=situacao)
    else:
        situacao = ""

    contexto = {
        "tickets": tickets,
        "situacao": situacao,
        "situacoes": Ticket.Situacao.choices,
        "tem_tickets": Ticket.objects.filter(cliente=request.user).exists(),
        "aguardando_resposta": Ticket.objects.filter(
            cliente=request.user, situacao=Ticket.Situacao.AGUARDANDO_CLIENTE
        ).count(),
    }
    return render(request, "tickets/meus_tickets.html", contexto)


@somente_cliente
def novo_ticket(request):
    """Abrir ticket (RF06)."""
    form = NovoTicketForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            ticket = services.abrir_ticket(request.user, **form.cleaned_data)
        except services.RegraDeNegocioError as erro:
            form.add_error(None, str(erro))
        else:
            messages.success(request, f"Ticket {ticket.numero} enviado. Você vai acompanhar o atendimento por aqui.")
            return redirect("tickets:meus_tickets")
    return render(request, "tickets/novo_ticket.html", {"form": form})


@somente_cliente
def ticket_cliente(request, numero):
    """
    Detalhe do ticket para o cliente (RF09) e resposta (RF12).
    O filtro por cliente faz o ticket de outra pessoa dar "não encontrado" (RN08, RNF04).
    """
    ticket = get_object_or_404(
        Ticket.objects.select_related("categoria", "atendente", "cliente"), pk=numero, cliente=request.user
    )
    form = RespostaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            services.responder(ticket, request.user, form.cleaned_data["texto"])
        except services.RegraDeNegocioError as erro:
            messages.error(request, str(erro))
        else:
            messages.success(request, "Mensagem enviada. A equipe de suporte será avisada.")
        return redirect("tickets:ticket_cliente", numero=ticket.pk)

    contexto = {
        "ticket": ticket,
        "conversa": services.linha_do_tempo(ticket, para_equipe=False),
        "form": form,
    }
    return render(request, "tickets/ticket_cliente.html", contexto)


# ---------- Equipe ----------

TICKETS_POR_PAGINA = 20


@somente_equipe
def fila(request):
    """
    Fila de atendimento (RF08): atrasados primeiro, depois o prazo mais próximo (RN10),
    com contadores por situação e filtros combináveis. Paginada para continuar rápida com
    muitos tickets (RNF07).
    """
    filtro = FiltroFilaForm(request.GET)
    tickets = services.fila_de_atendimento(request.user, **filtro.filtros)
    pagina = Paginator(tickets, TICKETS_POR_PAGINA).get_page(request.GET.get("pagina"))

    # Mantém os filtros nos links de paginação.
    parametros = request.GET.copy()
    parametros.pop("pagina", None)

    contexto = {
        "filtro": filtro,
        "pagina": pagina,
        "contadores": services.contadores_da_fila(),
        "parametros": parametros.urlencode(),
        "situacao_atual": filtro.filtros.get("situacao", ""),
        "so_atrasados": filtro.filtros.get("so_atrasados", False),
    }
    return render(request, "tickets/fila.html", contexto)


def _ticket_da_equipe(numero):
    return get_object_or_404(Ticket.objects.select_related("categoria", "atendente", "cliente"), pk=numero)


@somente_equipe
def ticket_equipe(request, numero):
    """
    Ticket na visão da equipe (RF09): conversa completa, inclusive notas internas,
    resposta ao cliente (RF12) e o painel "Gerenciar ticket" (RF10, RF11).
    """
    ticket = _ticket_da_equipe(numero)
    pode_atuar = services.pode_atuar(request.user, ticket)
    form = RespostaForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            services.responder(ticket, request.user, form.cleaned_data["texto"])
        except services.RegraDeNegocioError as erro:
            messages.error(request, str(erro))
        else:
            messages.success(request, "Mensagem enviada ao cliente.")
        return redirect("tickets:ticket_equipe", numero=ticket.pk)

    eh_admin = request.user.perfil == request.user.Perfil.ADMINISTRADOR
    mostra_gerenciar = ticket.aceita_resposta and (pode_atuar or (eh_admin and ticket.atendente_id is None))
    contexto = {
        "ticket": ticket,
        "conversa": services.linha_do_tempo(ticket, para_equipe=True),
        "form": form,
        "pode_atuar": pode_atuar,
        "motivo": "" if pode_atuar else services.motivo_para_nao_atuar(request.user, ticket),
        "gerenciar": GerenciarTicketForm(ticket=ticket, usuario=request.user) if mostra_gerenciar else None,
    }
    return render(request, "tickets/ticket_equipe.html", contexto)


@somente_equipe
@require_POST
def assumir_ticket(request, numero):
    """RF10: botão Assumir, na fila ou no ticket. Leva para o ticket assumido."""
    ticket = _ticket_da_equipe(numero)
    try:
        services.assumir(ticket, request.user)
    except services.RegraDeNegocioError as erro:
        messages.error(request, str(erro))
    else:
        messages.success(request, f"Ticket {ticket.numero} assumido. Agora ele está com você.")
    return redirect("tickets:ticket_equipe", numero=ticket.pk)


@somente_equipe
@require_POST
def gerenciar_ticket(request, numero):
    """Painel Gerenciar ticket: o administrador troca o atendente (RF10); o responsável ou o administrador muda a situação (RF11)."""
    ticket = _ticket_da_equipe(numero)
    form = GerenciarTicketForm(request.POST, ticket=ticket, usuario=request.user)
    if not form.is_valid():
        messages.error(request, "Escolha uma opção válida e tente de novo.")
        return redirect("tickets:ticket_equipe", numero=ticket.pk)

    feito = []
    situacao_original = ticket.situacao  # passar um ticket Aberto já muda a situação (RN04)
    try:
        novo_atendente = form.cleaned_data.get("atendente")
        if novo_atendente and novo_atendente.pk != ticket.atendente_id:
            services.atribuir(ticket, request.user, novo_atendente)
            feito.append(f"ticket passado para {novo_atendente.nome}")
        nova = form.cleaned_data["situacao"]
        if nova != situacao_original:
            services.mudar_situacao(ticket, request.user, nova)
            feito.append(f"situação alterada para {ticket.get_situacao_display()}")
    except services.RegraDeNegocioError as erro:
        messages.error(request, str(erro))
    else:
        if feito:
            messages.success(request, "Alterações salvas: " + " e ".join(feito) + ".")
        else:
            messages.info(request, "Nada foi alterado.")
    return redirect("tickets:ticket_equipe", numero=ticket.pk)
