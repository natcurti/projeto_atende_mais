"""
Controle de acesso por perfil (RNF04).

Uso nas views:

    @somente_equipe
    def fila(request): ...

Sem login, o usuário é levado para a tela de entrada. Com login, mas com o perfil
errado, recebe a página "acesso negado" (erro 403).
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import Usuario


def perfil_requerido(*perfis):
    def decorador(view):
        @login_required
        @wraps(view)
        def view_protegida(request, *args, **kwargs):
            if request.user.perfil not in perfis:
                raise PermissionDenied("Seu perfil não tem acesso a esta página.")
            return view(request, *args, **kwargs)

        return view_protegida

    return decorador


somente_cliente = perfil_requerido(Usuario.Perfil.CLIENTE)
somente_equipe = perfil_requerido(Usuario.Perfil.ATENDENTE, Usuario.Perfil.ADMINISTRADOR)
somente_administrador = perfil_requerido(Usuario.Perfil.ADMINISTRADOR)
