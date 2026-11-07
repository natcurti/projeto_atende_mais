"""
Regras de negócio do atendimento (camada de serviços).

As views chamam estas funções em vez de decidir sozinhas, para cada regra
ficar em um lugar só e ser testada uma vez.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import BooleanField, Case, Count, Q, Value, When
from django.utils import timezone

from .models import Avaliacao, Historico, Mensagem, Ticket

# Situações em que o ticket ainda precisa da equipe.
SITUACOES_EM_ABERTO = (
    Ticket.Situacao.ABERTO, Ticket.Situacao.EM_ATENDIMENTO, Ticket.Situacao.AGUARDANDO_CLIENTE,
)

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
    RF13: com interna=True, é uma nota da equipe que o cliente nunca vê (RN08).
    RN06: se o cliente responde um ticket Aguardando cliente, ele volta para Em atendimento.
    """
    if not ticket.aceita_resposta:
        raise RegraDeNegocioError("Este ticket já foi resolvido e não recebe novas mensagens.")
    if autor.eh_cliente and autor.pk != ticket.cliente_id:
        raise RegraDeNegocioError("Clientes só respondem os próprios tickets.")
    if autor.eh_cliente and interna:
        raise RegraDeNegocioError("Clientes não escrevem notas internas.")
    # RN05 vale para o que o cliente vê. Uma nota interna não altera o ticket,
    # então qualquer pessoa da equipe pode deixar uma, mesmo em ticket de outra pessoa.
    if autor.eh_equipe and not interna and not pode_atuar(autor, ticket):
        raise RegraDeNegocioError(motivo_para_nao_atuar(autor, ticket))

    mensagem = Mensagem.objects.create(ticket=ticket, autor=autor, texto=texto.strip(), interna=interna)
    if interna:
        # Não atualiza "atualizado_em": o cliente não pode perceber movimento que não consegue ver.
        return mensagem

    if autor.eh_cliente and ticket.situacao == Ticket.Situacao.AGUARDANDO_CLIENTE:
        registrar_historico(
            ticket, autor, Historico.Campo.SITUACAO,
            ticket.situacao, Ticket.Situacao.EM_ATENDIMENTO, quando=mensagem.criada_em,
        )
        ticket.situacao = Ticket.Situacao.EM_ATENDIMENTO

    ticket.save()  # atualiza "atualizado_em", que ordena Meus tickets
    return mensagem


# ---------- Atendimento pela equipe (RF10, RF11) ----------

# RF11: mudanças de situação que a equipe pode fazer. Reabrir (RF15) e fechar (RN07) vêm depois do MVP.
TRANSICOES_DA_EQUIPE = {
    Ticket.Situacao.EM_ATENDIMENTO: [Ticket.Situacao.AGUARDANDO_CLIENTE, Ticket.Situacao.RESOLVIDO],
    Ticket.Situacao.AGUARDANDO_CLIENTE: [Ticket.Situacao.EM_ATENDIMENTO, Ticket.Situacao.RESOLVIDO],
}


def pode_atuar(usuario, ticket):
    """
    RN05: só o atendente responsável ou um administrador altera o ticket.
    Um ticket sem atendente (Aberto) precisa ser assumido antes.
    """
    if not usuario.eh_equipe or ticket.atendente_id is None:
        return False
    return usuario.pk == ticket.atendente_id or usuario.perfil == usuario.Perfil.ADMINISTRADOR


def motivo_para_nao_atuar(usuario, ticket):
    """Explica por que pode_atuar() é falso, em linguagem do usuário."""
    if ticket.atendente_id is None:
        return "Assuma o ticket antes de responder ou mudar a situação."
    return f"Este ticket está com {ticket.atendente.nome}. Só a pessoa responsável ou um administrador pode alterá-lo."


def situacoes_possiveis(ticket):
    """Situações para as quais a equipe pode levar o ticket agora."""
    return TRANSICOES_DA_EQUIPE.get(ticket.situacao, [])


def _equipe_ativa(usuario):
    return usuario is not None and usuario.eh_equipe and usuario.is_active


@transaction.atomic
def assumir(ticket, usuario):
    """RF10, RN04: o atendente pega um ticket Aberto; ele passa para Em atendimento."""
    if not _equipe_ativa(usuario):
        raise RegraDeNegocioError("Só a equipe de suporte assume tickets.")
    if ticket.situacao != Ticket.Situacao.ABERTO:
        if ticket.atendente_id == usuario.pk:
            raise RegraDeNegocioError("Este ticket já está com você.")
        raise RegraDeNegocioError(f"Este ticket já está com {ticket.atendente.nome}.")

    agora = timezone.now()
    registrar_historico(ticket, usuario, Historico.Campo.ATENDENTE, None, usuario.nome, quando=agora)
    registrar_historico(ticket, usuario, Historico.Campo.SITUACAO, ticket.situacao, Ticket.Situacao.EM_ATENDIMENTO, quando=agora)
    ticket.atendente = usuario
    ticket.situacao = Ticket.Situacao.EM_ATENDIMENTO
    ticket.save()
    return ticket


@transaction.atomic
def atribuir(ticket, administrador, novo_atendente):
    """RF10: o administrador passa o ticket para outra pessoa da equipe."""
    if administrador.perfil != administrador.Perfil.ADMINISTRADOR:
        raise RegraDeNegocioError("Só administradores passam tickets para outra pessoa.")
    if not _equipe_ativa(novo_atendente):
        raise RegraDeNegocioError("Escolha uma pessoa ativa da equipe de suporte.")
    if not ticket.aceita_resposta:
        raise RegraDeNegocioError("Tickets resolvidos ou fechados não mudam de atendente.")
    if ticket.atendente_id == novo_atendente.pk:
        return ticket

    agora = timezone.now()
    anterior = ticket.atendente.nome if ticket.atendente_id else None
    registrar_historico(ticket, administrador, Historico.Campo.ATENDENTE, anterior, novo_atendente.nome, quando=agora)
    if ticket.situacao == Ticket.Situacao.ABERTO:  # RN04: com atendente, deixa de estar Aberto
        registrar_historico(ticket, administrador, Historico.Campo.SITUACAO, ticket.situacao, Ticket.Situacao.EM_ATENDIMENTO, quando=agora)
        ticket.situacao = Ticket.Situacao.EM_ATENDIMENTO
    ticket.atendente = novo_atendente
    ticket.save()
    return ticket


@transaction.atomic
def mudar_situacao(ticket, usuario, nova):
    """RF11, RN05: o responsável ou um administrador muda a situação; Resolvido grava a data."""
    if not pode_atuar(usuario, ticket):
        raise RegraDeNegocioError(motivo_para_nao_atuar(usuario, ticket))
    if nova == ticket.situacao:
        return ticket
    if nova not in situacoes_possiveis(ticket):
        raise RegraDeNegocioError(
            f"Um ticket {ticket.get_situacao_display()} não pode passar para {Ticket.Situacao(nova).label}."
        )

    agora = timezone.now()
    registrar_historico(ticket, usuario, Historico.Campo.SITUACAO, ticket.situacao, nova, quando=agora)
    ticket.situacao = nova
    if nova == Ticket.Situacao.RESOLVIDO:
        ticket.resolvido_em = agora
    ticket.save()
    return ticket


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


# ---------- Fila de atendimento (RF08) ----------

def _atrasado_agora():
    """RN10: condição de atraso para usar em consultas ao banco."""
    return Q(situacao__in=SITUACOES_EM_ABERTO, prazo__lt=timezone.now())


def fila_de_atendimento(usuario, situacao="", categoria=None, prioridade="", atendente="", so_atrasados=False):
    """
    Tickets da fila, com os filtros combinados.

    - situacao: "" para todos os que ainda precisam da equipe, ou uma situação específica.
    - atendente: "" (todos), "comigo", "sem" (sem atendente) ou o id de um usuário da equipe.
    - Ordem (RN10): atrasados primeiro, depois o prazo mais próximo.
      Resolvidos e fechados vêm do mais recente para o mais antigo.
    """
    tickets = Ticket.objects.select_related("cliente", "atendente", "categoria").annotate(
        esta_atrasado=Case(When(_atrasado_agora(), then=Value(True)), default=Value(False), output_field=BooleanField())
    )

    if situacao:
        tickets = tickets.filter(situacao=situacao)
    else:
        tickets = tickets.filter(situacao__in=SITUACOES_EM_ABERTO)
    if categoria:
        tickets = tickets.filter(categoria=categoria)
    if prioridade:
        tickets = tickets.filter(prioridade=prioridade)
    if atendente == "comigo":
        tickets = tickets.filter(atendente=usuario)
    elif atendente == "sem":
        tickets = tickets.filter(atendente__isnull=True)
    elif atendente:
        tickets = tickets.filter(atendente_id=atendente)
    if so_atrasados:
        tickets = tickets.filter(_atrasado_agora())

    if situacao in (Ticket.Situacao.RESOLVIDO, Ticket.Situacao.FECHADO):
        return tickets.order_by("-atualizado_em")
    return tickets.order_by("-esta_atrasado", "prazo", "id")


def contadores_da_fila():
    """Quantidade de tickets em cada situação em aberto e de atrasados, numa consulta só."""
    return Ticket.objects.aggregate(
        abertos=Count("id", filter=Q(situacao=Ticket.Situacao.ABERTO)),
        em_atendimento=Count("id", filter=Q(situacao=Ticket.Situacao.EM_ATENDIMENTO)),
        aguardando_cliente=Count("id", filter=Q(situacao=Ticket.Situacao.AGUARDANDO_CLIENTE)),
        atrasados=Count("id", filter=_atrasado_agora()),
    )


def pode_mudar_prioridade(usuario, ticket):
    """RF17: o responsável ou um administrador; o administrador também tria tickets ainda abertos."""
    if not ticket.aceita_resposta:
        return False
    return pode_atuar(usuario, ticket) or (usuario.eh_equipe and usuario.perfil == usuario.Perfil.ADMINISTRADOR)


@transaction.atomic
def mudar_prioridade(ticket, usuario, nova):
    """RF17, RN09: muda a prioridade e recalcula o prazo a partir da abertura do ticket."""
    if not ticket.aceita_resposta:
        raise RegraDeNegocioError("Tickets resolvidos ou fechados não mudam de prioridade.")
    if not pode_mudar_prioridade(usuario, ticket):
        raise RegraDeNegocioError(motivo_para_nao_atuar(usuario, ticket))
    if nova not in Ticket.Prioridade.values:
        raise RegraDeNegocioError("Prioridade inválida.")
    if nova == ticket.prioridade:
        return ticket

    registrar_historico(ticket, usuario, Historico.Campo.PRIORIDADE, ticket.prioridade, nova)
    ticket.prioridade = nova
    ticket.prazo = calcular_prazo(nova, ticket.aberto_em)
    ticket.save()
    return ticket


# ---------- Avaliação do atendimento (RF16) ----------

def pode_avaliar(usuario, ticket):
    """RN11: só a cliente dona do ticket, depois de resolvido, e uma única vez."""
    return (
        usuario.pk == ticket.cliente_id
        and ticket.situacao in (Ticket.Situacao.RESOLVIDO, Ticket.Situacao.FECHADO)
        and not Avaliacao.objects.filter(ticket=ticket).exists()
    )


def avaliar(ticket, cliente, nota, comentario=""):
    """RF16, RN11: a cliente dá uma nota de 1 a 5 e, se quiser, um comentário."""
    if cliente.pk != ticket.cliente_id:
        raise RegraDeNegocioError("Só quem abriu o ticket pode avaliar o atendimento.")
    if ticket.situacao not in (Ticket.Situacao.RESOLVIDO, Ticket.Situacao.FECHADO):
        raise RegraDeNegocioError("O atendimento só pode ser avaliado depois que o ticket for resolvido.")
    if Avaliacao.objects.filter(ticket=ticket).exists():
        raise RegraDeNegocioError("Este atendimento já foi avaliado. A avaliação só pode ser feita uma vez.")
    if nota not in range(1, 6):
        raise RegraDeNegocioError("Escolha uma nota de 1 a 5.")
    return Avaliacao.objects.create(ticket=ticket, nota=nota, comentario=(comentario or "").strip() or None)
