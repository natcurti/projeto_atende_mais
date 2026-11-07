from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from tickets.forms import CategoriaForm
from tickets.models import Categoria

from . import services
from .forms import CadastroClienteForm, EntrarForm, PessoaEquipeForm
from .models import Usuario
from .permissoes import somente_administrador


def pagina_inicial_do_perfil(usuario):
    """Cada perfil começa numa tela diferente (navegação da Entrega 3)."""
    if usuario.eh_cliente:
        return reverse("tickets:meus_tickets")
    return reverse("tickets:fila")


def inicio(request):
    """Endereço raiz: leva cada pessoa para o lugar certo."""
    if request.user.is_authenticated:
        return redirect(pagina_inicial_do_perfil(request.user))
    return redirect("contas:entrada")


def _destino_seguro(request, usuario):
    """Volta para a página que a pessoa tentou abrir antes do login, se for deste site."""
    proximo = request.POST.get("next") or request.GET.get("next")
    if proximo and url_has_allowed_host_and_scheme(proximo, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return proximo
    return pagina_inicial_do_perfil(usuario)


def entrada(request):
    """Tela de entrada: login (RF02) e cadastro de cliente (RF01) na mesma página, como no protótipo."""
    if request.user.is_authenticated:
        return redirect(pagina_inicial_do_perfil(request.user))

    form_entrar = EntrarForm(request)
    form_cadastro = CadastroClienteForm()

    if request.method == "POST":
        if request.POST.get("acao") == "cadastrar":
            form_cadastro = CadastroClienteForm(request.POST)
            if form_cadastro.is_valid():
                usuario = form_cadastro.save()
                login(request, usuario)
                messages.success(request, "Conta criada. Quando precisar de ajuda, abra um ticket.")
                return redirect(pagina_inicial_do_perfil(usuario))
        else:
            form_entrar = EntrarForm(request, data=request.POST)
            if form_entrar.is_valid():
                usuario = form_entrar.get_user()
                login(request, usuario)
                return redirect(_destino_seguro(request, usuario))

    contexto = {
        "form_entrar": form_entrar,
        "form_cadastro": form_cadastro,
        "next": request.POST.get("next") or request.GET.get("next", ""),
        "modo_demonstracao": settings.DEBUG,
    }
    return render(request, "contas/entrada.html", contexto)


@require_POST
def sair(request):
    """Encerra a sessão. Só aceita POST, para um link externo não conseguir deslogar alguém."""
    logout(request)
    messages.info(request, "Você saiu do atende+.")
    return redirect("contas:entrada")


# ---------- Administração (RF04, RF05) ----------

@somente_administrador
def administracao(request):
    """Página Administração: equipe de suporte e categorias de ticket."""
    contexto = {
        "equipe": services.equipe(),
        "categorias": Categoria.objects.order_by("-ativa", "nome"),
        "form_categoria": CategoriaForm(),
    }
    return render(request, "contas/administracao.html", contexto)


def _pessoa_da_equipe(pk):
    """Clientes não aparecem aqui: o endereço de um cliente dá "não encontrado"."""
    return get_object_or_404(Usuario, pk=pk, perfil__in=services.PERFIS_DA_EQUIPE)


@somente_administrador
def nova_pessoa(request):
    """RF04: cadastra um atendente ou administrador."""
    form = PessoaEquipeForm(request.POST or None, editor=request.user)
    if request.method == "POST" and form.is_valid():
        pessoa = form.save()
        messages.success(request, f"{pessoa.nome} agora faz parte da equipe e já pode entrar com o e-mail e a senha inicial.")
        return redirect("contas:administracao")
    return render(request, "contas/pessoa_form.html", {"form": form})


@somente_administrador
def editar_pessoa(request, pk):
    """RF04: edita nome, e-mail, perfil e, se quiser, a senha."""
    pessoa = _pessoa_da_equipe(pk)
    form = PessoaEquipeForm(request.POST or None, instance=pessoa, editor=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Dados de {pessoa.nome} salvos.")
        return redirect("contas:administracao")
    return render(request, "contas/pessoa_form.html", {"form": form, "pessoa": pessoa})


@somente_administrador
@require_POST
def alterar_acesso(request, pk):
    """RN12: desativa ou reativa o acesso de uma pessoa da equipe. Ninguém é excluído."""
    pessoa = _pessoa_da_equipe(pk)
    ativar = not pessoa.is_active
    try:
        em_aberto = services.alterar_acesso(request.user, pessoa, ativar)
    except services.AdministracaoError as erro:
        messages.error(request, str(erro))
    else:
        if ativar:
            messages.success(request, f"O acesso de {pessoa.nome} foi reativado.")
        else:
            messages.success(request, f"O acesso de {pessoa.nome} foi desativado. O nome continua nos tickets antigos.")
            if em_aberto:
                messages.warning(
                    request,
                    f"{pessoa.nome} ainda tem {em_aberto} ticket{'s' if em_aberto > 1 else ''} em aberto. "
                    "Abra cada um na fila e passe para outra pessoa da equipe.",
                )
    return redirect("contas:administracao")
