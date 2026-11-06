"""
Regras de negócio do atendimento (camada de serviços).

As views chamam estas funções em vez de decidir sozinhas, para cada regra
ficar em um lugar só e ser testada uma vez. Novas regras (assumir ticket,
mudar situação, reabrir...) entram aqui a partir do MVP.
"""

from datetime import timedelta

# RN09: tempo para resolver o ticket, conforme a prioridade.
PRAZO_POR_PRIORIDADE = {
    "urgente": timedelta(hours=4),
    "alta": timedelta(days=1),
    "media": timedelta(days=3),
    "baixa": timedelta(days=5),
}


def calcular_prazo(prioridade, aberto_em):
    """Devolve a data limite de resolução de um ticket aberto em `aberto_em` (RN09)."""
    try:
        return aberto_em + PRAZO_POR_PRIORIDADE[prioridade]
    except KeyError:
        raise ValueError(f"Prioridade desconhecida: {prioridade!r}") from None
