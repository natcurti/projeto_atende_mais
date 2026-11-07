"""
Regras de negócio do atendimento (camada de serviços).

As views chamam estas funções em vez de decidir sozinhas, para cada regra
ficar em um lugar só e ser testada uma vez.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from .models import Historico, Mensagem, Ticket

# RN09: tempo para resolver o ticket, conforme a prioridade.
PRAZO_POR_PRIORIDADE = {
    "urgente": timedelta(hours=4),
    "alta": timedelta(days=1),
    "media": timedelta(days=3),
    "baixa": timedelta(days=5),
}


class RegraDeNegocioError(Exception):
    """Ação recusada por uma regra de negócio. A mensagem é mostrada para o usuário."""


def calcular_prazo(prioridade, aberto_em):
    """Devolve a data limite de resolução de um ticket aberto em `aberto_em` (RN09)."""
    try:
        return aberto_em + PRAZO_POR_PRIORIDADE[prioridade]
    except KeyError:
        raise ValueError(f"Prioridade desconhecida: {prioridade!r}") from None


def registrar_historico(ticket, autor, campo, anterior, novo, quando=None):
    """RN13: grava uma mudança do ticket. Não grava nada se o valor não mudou."""
    if anterior == novo:
        return None
    return Historico.objects.create(
        ticket=ticket, autor=autor, campo=campo,
        valor_anterior=anterior, valor_novo=novo, alterado_em=quando or timezone.now(),
    )


def abrir_ticket(cliente, titulo, descricao, categoria):
    """
    RF06: o cliente abre um ticket.
    Ele nasce Aberto, sem atendente (RN03), com prioridade Média e prazo calculado (RN09).
    O número vem do banco, a partir de 1000 (RN01).
    """
    if not cliente.eh_cliente:
        raise RegraDeNegocioError("Só clientes abrem tickets.")
    if not categoria.ativa:
        raise RegraDeNegocioError("Esta categoria não está mais disponível. Escolha outra.")
    return Ticket.objects.create(cliente=cliente, titulo=titulo, descricao=descricao, categoria=categoria)


@transaction.atomic
def responder(ticket, autor, texto, interna=False):
    """
    RF12: adiciona uma mensagem à conversa do ticket.
    RN06: se o cliente responde um ticket Aguardando cliente, ele volta para Em atendimento.
    """
    if not ticket.aceita_resposta:
        raise RegraDeNegocioError("Este ticket já foi resolvido e não recebe novas mensagens.")
    if autor.eh_cliente and autor.pk != ticket.cliente_id:
        raise RegraDeNegocioError("Clientes só respondem os próprios tickets.")
    if autor.eh_cliente and interna:
        raise RegraDeNegocioError("Clientes não escrevem notas internas.")

    mensagem = Mensagem.objects.create(ticket=ticket, autor=autor, texto=texto.strip(), interna=interna)

    if autor.eh_cliente and ticket.situacao == Ticket.Situacao.AGUARDANDO_CLIENTE:
        registrar_historico(
            ticket, autor, Historico.Campo.SITUACAO,
            ticket.situacao, Ticket.Situacao.EM_ATENDIMENTO, quando=mensagem.criada_em,
        )
        ticket.situacao = Ticket.Situacao.EM_ATENDIMENTO

    ticket.save()  # atualiza "atualizado_em", que ordena Meus tickets
    return mensagem


@dataclass
class ItemDaConversa:
    """Uma linha da conversa do ticket: mensagem ou evento do histórico."""

    tipo: str  # "mensagem" ou "evento"
    quando: datetime
    texto: str
    autor: object = None
    da_equipe: bool = False
    interna: bool = False


def linha_do_tempo(ticket, para_equipe):
    """
    RF09: conversa do ticket em ordem cronológica: a descrição inicial, as mensagens
    e os eventos do histórico. Para o cliente, as notas internas ficam de fora (RN08).
    """
    itens = [ItemDaConversa("mensagem", ticket.aberto_em, ticket.descricao, autor=ticket.cliente)]

    mensagens = ticket.mensagens.select_related("autor")
    if not para_equipe:
        mensagens = mensagens.filter(interna=False)
    for m in mensagens:
        itens.append(ItemDaConversa(
            "mensagem", m.criada_em, m.texto, autor=m.autor, da_equipe=m.autor.eh_equipe, interna=m.interna,
        ))

    for h in ticket.historico.select_related("autor"):
        itens.append(ItemDaConversa("evento", h.alterado_em, h.descricao))

    # Em caso de mesmo horário, o evento vem antes da mensagem (ex.: assumiu e depois respondeu).
    return sorted(itens, key=lambda item: (item.quando, item.tipo == "mensagem"))
