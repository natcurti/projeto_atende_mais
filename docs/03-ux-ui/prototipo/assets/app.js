// atende+ — interações do protótipo navegável (Entrega 3)
// Nada aqui salva dados: é só para simular o comportamento das telas.

(function () {
  var params = new URLSearchParams(window.location.search);

  // 1. Avisos de confirmação: a URL traz ?aviso=nome e a tela mostra o aviso
  //    com data-aviso="nome" (ex.: depois de enviar um ticket).
  var aviso = params.get('aviso');
  if (aviso) {
    var alvo = document.querySelector('[data-aviso="' + aviso + '"]');
    if (alvo) {
      alvo.hidden = false;
      alvo.setAttribute('tabindex', '-1');
      alvo.focus();
    }
  }

  // 2. Perfil do protótipo: o atalho "Entrar como administrador" guarda o perfil,
  //    e as telas da equipe mostram os itens exclusivos do administrador.
  document.querySelectorAll('[data-perfil]').forEach(function (link) {
    link.addEventListener('click', function () {
      try { sessionStorage.setItem('atende-perfil', link.dataset.perfil); } catch (e) {}
    });
  });
  var perfil = null;
  try { perfil = sessionStorage.getItem('atende-perfil'); } catch (e) {}
  if (perfil === 'admin') {
    document.querySelectorAll('[data-so-admin]').forEach(function (el) { el.hidden = false; });
    document.querySelectorAll('[data-nome-usuario]').forEach(function (el) {
      el.innerHTML = 'Juliana Prado <small>Administradora</small>';
    });
  }

  // 3. Alternador "Mensagem ao cliente" / "Nota interna".
  document.querySelectorAll('.alternador').forEach(function (grupo) {
    var form = grupo.closest('form');
    var botoes = grupo.querySelectorAll('button');
    botoes.forEach(function (botao) {
      botao.addEventListener('click', function () {
        botoes.forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
        botao.setAttribute('aria-pressed', 'true');
        var interno = botao.dataset.modo === 'interna';
        form.classList.toggle('modo-interno', interno);
        var rotulo = form.querySelector('[data-rotulo-mensagem]');
        var enviar = form.querySelector('[data-botao-enviar]');
        if (rotulo) rotulo.textContent = interno ? 'Nota interna (o cliente não vê)' : 'Mensagem ao cliente';
        if (enviar) enviar.textContent = interno ? 'Salvar nota interna' : 'Enviar mensagem';
      });
    });
  });

  // 4. Avaliação por estrelas (1 a 5).
  document.querySelectorAll('.estrelas').forEach(function (grupo) {
    var estrelas = grupo.querySelectorAll('button');
    var saida = document.querySelector('[data-nota-escolhida]');
    estrelas.forEach(function (estrela, i) {
      estrela.addEventListener('click', function () {
        estrelas.forEach(function (e, j) {
          e.classList.toggle('ativa', j <= i);
          e.setAttribute('aria-pressed', j === i ? 'true' : 'false');
        });
        if (saida) saida.textContent = 'Nota escolhida: ' + (i + 1) + ' de 5';
      });
    });
  });
})();
