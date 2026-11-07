from django.shortcuts import render

from contas.permissoes import somente_administrador

from . import services


@somente_administrador
def painel(request):
    """Painel de indicadores (RF18): só para administradores."""
    try:
        dias = int(request.GET.get("dias", services.PERIODO_PADRAO))
    except ValueError:
        dias = services.PERIODO_PADRAO
    if dias not in services.PERIODOS_EM_DIAS:
        dias = services.PERIODO_PADRAO

    contexto = {
        "ind": services.calcular(dias),
        "periodos": services.PERIODOS_EM_DIAS,
        "passo_rotulo": {7: 1, 30: 5, 90: 15}[dias],  # de quantos em quantos dias mostrar a data no eixo
    }
    return render(request, "painel/painel.html", contexto)
