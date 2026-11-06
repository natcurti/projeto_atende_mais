from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CadastroClienteForm, EntrarForm


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
