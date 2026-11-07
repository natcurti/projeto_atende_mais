"""
Regras de negócio da administração da equipe (RF04, RN12).
Ninguém é excluído: pessoas são desativadas, e o histórico dos tickets continua com o nome delas.
"""

from .models import Usuario


class AdministracaoError(Exception):
    """Ação recusada. A mensagem é mostrada para o administrador."""


PERFIS_DA_EQUIPE = (Usuario.Perfil.ATENDENTE, Usuario.Perfil.ADMINISTRADOR)


def equipe():
    """Atendentes e administradores, ativos primeiro e depois por nome."""
    return Usuario.objects.filter(perfil__in=PERFIS_DA_EQUIPE).order_by("-is_active", "nome")


def tickets_em_aberto_de(pessoa):
    """Quantos tickets ainda dependem desta pessoa."""
    from tickets.models import Ticket

    return Ticket.objects.filter(
        atendente=pessoa,
        situacao__in=[Ticket.Situacao.EM_ATENDIMENTO, Ticket.Situacao.AGUARDANDO_CLIENTE],
    ).count()


def alterar_acesso(administrador, pessoa, ativo):
    """
    Desativa ou reativa uma pessoa da equipe (RN12).
    O administrador não pode desativar a si mesmo, para o sistema nunca ficar sem administrador ativo.
    Devolve quantos tickets em aberto a pessoa ainda tem (para o aviso na tela).
    """
    if pessoa.perfil not in PERFIS_DA_EQUIPE:
        raise AdministracaoError("Só pessoas da equipe são gerenciadas aqui.")
    if not ativo and pessoa.pk == administrador.pk:
        raise AdministracaoError("Você não pode desativar o seu próprio acesso.")
    pessoa.is_active = ativo
    pessoa.save(update_fields=["is_active"])
    return tickets_em_aberto_de(pessoa)
