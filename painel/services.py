"""
Indicadores do atendimento (RF18).

Cada função responde a uma pergunta da gestão. O período vale para o que aconteceu nele:
tickets abertos, resolvidos e avaliados nos últimos N dias. "Em aberto" e "atrasados"
são uma foto de agora, independentes do período.
"""

from dataclasses import dataclass, field
from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone

from contas.models import Usuario
from tickets.models import Avaliacao, Categoria, Ticket
from tickets.services import SITUACOES_EM_ABERTO

PERIODOS_EM_DIAS = (7, 30, 90)
PERIODO_PADRAO = 30


def horas(intervalo):
    return intervalo.total_seconds() / 3600


@dataclass
class Indicadores:
    dias: int
    inicio: object
    em_aberto: int = 0
    atrasados: int = 0
    abertos_no_periodo: int = 0
    resolvidos_no_periodo: int = 0
    tempo_medio_horas: float | None = None
    no_prazo_percentual: int | None = None
    nota_media: float | None = None
    avaliacoes: int = 0
    abertos_por_dia: list = field(default_factory=list)
    por_categoria: list = field(default_factory=list)
    por_atendente: list = field(default_factory=list)

    @property
    def maior_dia(self):
        return max((d["quantidade"] for d in self.abertos_por_dia), default=0)


def _resolucoes(tickets):
    """Tempo de resolução (horas) e se ficou dentro do prazo, de cada ticket resolvido."""
    return [(horas(t.resolvido_em - t.aberto_em), t.resolvido_em <= t.prazo) for t in tickets]


def _media(valores):
    return round(sum(valores) / len(valores), 1) if valores else None


def calcular(dias=PERIODO_PADRAO):
    agora = timezone.now()
    inicio = agora - timedelta(days=dias)
    ind = Indicadores(dias=dias, inicio=inicio)

    # Foto de agora
    ind.em_aberto = Ticket.objects.filter(situacao__in=SITUACOES_EM_ABERTO).count()
    ind.atrasados = Ticket.objects.filter(situacao__in=SITUACOES_EM_ABERTO, prazo__lt=agora).count()

    # No período
    abertos = Ticket.objects.filter(aberto_em__gte=inicio)
    resolvidos = list(
        Ticket.objects.filter(resolvido_em__gte=inicio).only("aberto_em", "resolvido_em", "prazo", "categoria", "atendente")
    )
    ind.abertos_no_periodo = abertos.count()
    ind.resolvidos_no_periodo = len(resolvidos)
    resolucoes = _resolucoes(resolvidos)
    ind.tempo_medio_horas = _media([h for h, _ in resolucoes])
    if resolucoes:
        ind.no_prazo_percentual = round(100 * sum(1 for _, ok in resolucoes if ok) / len(resolucoes))

    avaliacoes = Avaliacao.objects.filter(avaliado_em__gte=inicio)
    resumo = avaliacoes.aggregate(media=Avg("nota"), total=Count("id"))
    ind.avaliacoes = resumo["total"]
    ind.nota_media = round(resumo["media"], 1) if resumo["media"] is not None else None

    ind.abertos_por_dia = _abertos_por_dia(abertos, dias, agora)
    ind.por_categoria = _por_categoria(inicio, resolvidos)
    ind.por_atendente = _por_atendente(inicio, resolvidos, agora)
    return ind


def _abertos_por_dia(abertos, dias, agora):
    """Uma entrada por dia do período, inclusive os dias sem nenhum ticket (horário de Brasília)."""
    contagem = {}
    for aberto_em in abertos.values_list("aberto_em", flat=True):
        dia = timezone.localtime(aberto_em).date()
        contagem[dia] = contagem.get(dia, 0) + 1
    hoje = timezone.localtime(agora).date()
    return [
        {"dia": dia, "quantidade": contagem.get(dia, 0)}
        for dia in (hoje - timedelta(days=n) for n in range(dias - 1, -1, -1))
    ]


def _por_categoria(inicio, resolvidos):
    abertos = dict(
        Ticket.objects.filter(aberto_em__gte=inicio).values("categoria").annotate(n=Count("id")).values_list("categoria", "n")
    )
    linhas = []
    for categoria in Categoria.objects.order_by("nome"):
        dela = [t for t in resolvidos if t.categoria_id == categoria.pk]
        if not abertos.get(categoria.pk) and not dela:
            continue
        linhas.append({
            "nome": categoria.nome,
            "abertos": abertos.get(categoria.pk, 0),
            "resolvidos": len(dela),
            "tempo_medio_horas": _media([h for h, _ in _resolucoes(dela)]),
        })
    return sorted(linhas, key=lambda linha: -linha["abertos"])


def _por_atendente(inicio, resolvidos, agora):
    equipe = Usuario.objects.filter(
        perfil__in=[Usuario.Perfil.ATENDENTE, Usuario.Perfil.ADMINISTRADOR]
    ).annotate(
        em_aberto=Count("tickets_atendidos", filter=Q(tickets_atendidos__situacao__in=SITUACOES_EM_ABERTO)),
        atrasados=Count(
            "tickets_atendidos",
            filter=Q(tickets_atendidos__situacao__in=SITUACOES_EM_ABERTO, tickets_atendidos__prazo__lt=agora),
        ),
    )
    notas = dict(
        Avaliacao.objects.filter(avaliado_em__gte=inicio)
        .values("ticket__atendente").annotate(media=Avg("nota")).values_list("ticket__atendente", "media")
    )
    linhas = []
    for pessoa in equipe:
        dela = [t for t in resolvidos if t.atendente_id == pessoa.pk]
        if not dela and not pessoa.em_aberto:
            continue
        resolucoes = _resolucoes(dela)
        linhas.append({
            "nome": pessoa.nome,
            "ativo": pessoa.is_active,
            "em_aberto": pessoa.em_aberto,
            "atrasados": pessoa.atrasados,
            "resolvidos": len(dela),
            "tempo_medio_horas": _media([h for h, _ in resolucoes]),
            "no_prazo_percentual": round(100 * sum(1 for _, ok in resolucoes if ok) / len(resolucoes)) if resolucoes else None,
            "nota_media": round(notas[pessoa.pk], 1) if pessoa.pk in notas else None,
        })
    return sorted(linhas, key=lambda linha: (-linha["resolvidos"], linha["nome"]))
