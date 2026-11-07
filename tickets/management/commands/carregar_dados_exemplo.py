"""
Carrega os dados de exemplo do atende+ (os mesmos do protótipo da Entrega 3).

Uso:  python manage.py carregar_dados_exemplo

As datas são calculadas a partir do momento em que o comando roda,
para sempre haver tickets recentes e um ticket atrasado na demonstração.
Para recomeçar do zero: apague o arquivo db.sqlite3 e rode `migrate` de novo.
"""

import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from tickets.models import Avaliacao, Categoria, Historico, Mensagem, Ticket

SENHA_DEMONSTRACAO = "atende123"


class Command(BaseCommand):
    help = "Carrega usuários, categorias e tickets de exemplo para demonstração."

    @transaction.atomic
    def handle(self, *args, **options):
        Usuario = get_user_model()
        if Usuario.objects.exists() or Ticket.objects.exists():
            raise CommandError(
                "O banco já tem dados. Para recomeçar, apague o arquivo db.sqlite3 e rode "
                "`python manage.py migrate` antes deste comando."
            )

        agora = timezone.now()
        P = Usuario.Perfil

        # --- Usuários ---
        juliana = Usuario.objects.create_superuser("juliana@empresa.com", SENHA_DEMONSTRACAO, nome="Juliana Prado")
        carlos = Usuario.objects.create_user("carlos@empresa.com", SENHA_DEMONSTRACAO, nome="Carlos Lima", perfil=P.ATENDENTE)
        ana = Usuario.objects.create_user("ana@empresa.com", SENHA_DEMONSTRACAO, nome="Ana Reis", perfil=P.ATENDENTE)
        Usuario.objects.create_user(
            "pedro@empresa.com", SENHA_DEMONSTRACAO, nome="Pedro Alves", perfil=P.ATENDENTE, is_active=False
        )
        maria = Usuario.objects.create_user(
            "maria@souzacomercio.com.br", SENHA_DEMONSTRACAO, nome="Maria Souza", empresa="Souza Comércio ME"
        )
        roberto = Usuario.objects.create_user(
            "roberto@padariabompao.com.br", SENHA_DEMONSTRACAO, nome="Roberto Dias", empresa="Padaria Bom Pão"
        )
        fernanda = Usuario.objects.create_user(
            "fernanda@lojacentral.com.br", SENHA_DEMONSTRACAO, nome="Fernanda Lopes", empresa="Loja Central"
        )
        jose = Usuario.objects.create_user(
            "jose@autopecassilva.com.br", SENHA_DEMONSTRACAO, nome="José Silva", empresa="Auto Peças Silva"
        )

        # --- Categorias ---
        erro = Categoria.objects.create(nome="Erro no sistema")
        duvida = Categoria.objects.create(nome="Dúvida")
        financeiro = Categoria.objects.create(nome="Financeiro")
        Categoria.objects.create(nome="Treinamento", ativa=False)

        # --- Tickets (criados nesta ordem, recebem os números 1000 a 1006) ---
        S, PR = Ticket.Situacao, Ticket.Prioridade

        def ticket(**dados):
            return Ticket.objects.create(**dados)

        t1000 = ticket(
            titulo="Não consigo cadastrar produto", descricao="O botão Salvar fica desabilitado na tela de produtos.",
            cliente=maria, categoria=erro, prioridade=PR.ALTA, situacao=S.FECHADO, atendente=ana,
            aberto_em=agora - timedelta(days=13), resolvido_em=agora - timedelta(days=12), fechado_em=agora - timedelta(days=5),
        )
        t1001 = ticket(
            titulo="Cobrança duplicada em outubro", descricao="O boleto de outubro veio duas vezes no mesmo valor. Paguei só um.",
            cliente=maria, categoria=financeiro, situacao=S.RESOLVIDO, atendente=ana,
            aberto_em=agora - timedelta(days=5), resolvido_em=agora - timedelta(days=3),
        )
        t1002 = ticket(
            titulo="Dúvida sobre o relatório mensal", descricao="O relatório mensal mostra vendas canceladas. Isso está certo?",
            cliente=maria, categoria=duvida, prioridade=PR.BAIXA, situacao=S.AGUARDANDO_CLIENTE, atendente=carlos,
            aberto_em=agora - timedelta(days=2),
        )
        t1003 = ticket(
            titulo="Erro ao emitir nota fiscal",
            descricao='Ao clicar em "Emitir nota", aparece a mensagem "Falha na comunicação com a SEFAZ". Já tentei três vezes.',
            cliente=maria, categoria=erro, situacao=S.EM_ATENDIMENTO, atendente=carlos,
            aberto_em=agora - timedelta(days=1, hours=3),
        )
        t1004 = ticket(
            titulo="Boleto não chegou por e-mail", descricao="O boleto de novembro não chegou no e-mail do financeiro.",
            cliente=jose, categoria=financeiro, prioridade=PR.BAIXA, situacao=S.AGUARDANDO_CLIENTE, atendente=ana,
            aberto_em=agora - timedelta(days=1),
        )
        ticket(
            titulo="Como cadastrar um novo usuário?",
            descricao="Contratamos uma pessoa nova e não achamos onde criar o acesso dela.",
            cliente=fernanda, categoria=duvida, aberto_em=agora - timedelta(hours=1),
        )
        ticket(
            titulo="Sistema lento ao gerar relatório",
            descricao="Desde ontem o relatório de vendas leva mais de 5 minutos para abrir.",
            cliente=roberto, categoria=erro, prioridade=PR.URGENTE,
            aberto_em=agora - timedelta(hours=6),  # prazo de 4 horas: já está atrasado (RN10)
        )

        def assumiu(t, atendente, quando):
            """Registra no histórico que o atendente assumiu o ticket (RN04, RN13)."""
            Historico.objects.create(ticket=t, autor=atendente, campo="atendente", valor_novo=atendente.nome, alterado_em=quando)
            Historico.objects.create(
                ticket=t, autor=atendente, campo="situacao", valor_anterior=S.ABERTO, valor_novo=S.EM_ATENDIMENTO,
                alterado_em=quando,
            )

        # --- Conversa e histórico do ticket #1003 ---
        assumido = t1003.aberto_em + timedelta(minutes=32)
        assumiu(t1003, carlos, assumido)
        Mensagem.objects.create(
            ticket=t1003, autor=carlos, interna=True, criada_em=assumido + timedelta(minutes=2),
            texto="Parece o mesmo caso do certificado digital vencido. Confirmar com o print antes de responder.",
        )
        Mensagem.objects.create(
            ticket=t1003, autor=carlos, criada_em=assumido + timedelta(minutes=3),
            texto="Olá, Maria! Pode nos enviar um print da tela com o erro? Assim confirmamos a causa.",
        )
        Mensagem.objects.create(ticket=t1003, autor=maria, criada_em=agora - timedelta(hours=2), texto="Segue o print.")

        # --- #1000 (fechado) ---
        assumiu(t1000, ana, t1000.aberto_em + timedelta(hours=1))
        Mensagem.objects.create(
            ticket=t1000, autor=ana, criada_em=t1000.resolvido_em,
            texto="Maria, liberamos o cadastro de produtos na sua conta. Pode testar de novo?",
        )
        Historico.objects.create(
            ticket=t1000, autor=ana, campo="situacao", valor_anterior=S.EM_ATENDIMENTO, valor_novo=S.RESOLVIDO,
            alterado_em=t1000.resolvido_em,
        )
        Historico.objects.create(
            ticket=t1000, autor=ana, campo="situacao", valor_anterior=S.RESOLVIDO, valor_novo=S.FECHADO,
            alterado_em=t1000.fechado_em,
        )

        # --- #1001 (resolvido) ---
        assumiu(t1001, ana, t1001.aberto_em + timedelta(hours=1))
        Mensagem.objects.create(
            ticket=t1001, autor=ana, criada_em=t1001.resolvido_em,
            texto="Maria, confirmamos a duplicidade e cancelamos o segundo boleto. Não há nada pendente na sua conta.",
        )
        Historico.objects.create(
            ticket=t1001, autor=ana, campo="situacao", valor_anterior=S.EM_ATENDIMENTO, valor_novo=S.RESOLVIDO,
            alterado_em=t1001.resolvido_em,
        )

        # --- #1002 (aguardando a cliente) ---
        pergunta = t1002.aberto_em + timedelta(hours=5)
        assumiu(t1002, carlos, pergunta - timedelta(minutes=10))
        Mensagem.objects.create(
            ticket=t1002, autor=carlos, criada_em=pergunta, texto="Olá! Pode nos dizer de qual mês é o relatório?",
        )
        Historico.objects.create(
            ticket=t1002, autor=carlos, campo="situacao", valor_anterior=S.EM_ATENDIMENTO, valor_novo=S.AGUARDANDO_CLIENTE,
            alterado_em=pergunta,
        )

        # --- #1004 (aguardando o cliente) ---
        pergunta = t1004.aberto_em + timedelta(hours=3)
        assumiu(t1004, ana, pergunta - timedelta(minutes=5))
        Mensagem.objects.create(
            ticket=t1004, autor=ana, criada_em=pergunta,
            texto="José, o boleto foi enviado para financeiro@autopecassilva.com.br. Esse é o e-mail certo?",
        )
        Historico.objects.create(
            ticket=t1004, autor=ana, campo="situacao", valor_anterior=S.EM_ATENDIMENTO, valor_novo=S.AGUARDANDO_CLIENTE,
            alterado_em=pergunta,
        )

        # --- Avaliações (o #1001 fica sem, para a Maria avaliar na demonstração) ---
        Avaliacao.objects.create(ticket=t1000, nota=4, comentario="Resolveram rápido.", avaliado_em=t1000.resolvido_em + timedelta(hours=2))

        # --- Histórico para o painel de indicadores (RF18) ---
        self._historico(agora, [roberto, fernanda, jose], [carlos, ana, juliana], [erro, duvida, financeiro])

        # "Última atualização" de cada ticket = o último acontecimento dele (mensagem ou mudança).
        for t in Ticket.objects.all():
            datas = [t.aberto_em, *t.mensagens.values_list("criada_em", flat=True),
                     *t.historico.values_list("alterado_em", flat=True)]
            Ticket.objects.filter(pk=t.pk).update(atualizado_em=max(datas))

        self.stdout.write(self.style.SUCCESS(
            f"Dados de exemplo carregados: {Usuario.objects.count()} usuários, "
            f"{Categoria.objects.count()} categorias e {Ticket.objects.count()} tickets."
        ))
        self.stdout.write(f"Todos os usuários entram com a senha: {SENHA_DEMONSTRACAO}")
        self.stdout.write(f"Área técnica (/admin): {juliana.email}")

    def _historico(self, agora, clientes, equipe, categorias):
        """
        45 tickets já resolvidos ou fechados nos últimos 40 dias, para o painel ter o que mostrar.
        Usa sempre a mesma semente: os números saem iguais em qualquer máquina.
        """
        sorteio = random.Random(2026)
        S = Ticket.Situacao
        # Horas típicas de resolução por categoria: dúvidas são rápidas, erros demoram mais.
        horas_tipicas = {"Dúvida": (1, 20), "Financeiro": (4, 40), "Erro no sistema": (6, 90)}
        assuntos = {
            "Dúvida": ["Como exportar o relatório?", "Onde altero meu e-mail?", "Como emitir segunda via?", "Dúvida sobre permissões"],
            "Financeiro": ["Boleto com valor errado", "Nota fiscal não chegou", "Cobrança em duplicidade", "Mudança de forma de pagamento"],
            "Erro no sistema": ["Tela de vendas não carrega", "Erro ao salvar cliente", "Relatório sai em branco", "Sistema lento pela manhã"],
        }
        for _ in range(45):
            categoria = sorteio.choice(categorias)
            prioridade = sorteio.choices(["urgente", "alta", "media", "baixa"], weights=[1, 3, 5, 2])[0]
            aberto_em = agora - timedelta(days=sorteio.uniform(3, 40))
            minimo, maximo = horas_tipicas[categoria.nome]
            resolvido_em = aberto_em + timedelta(hours=sorteio.uniform(minimo, maximo))
            atendente = sorteio.choices(equipe, weights=[5, 4, 1])[0]
            fechado = resolvido_em < agora - timedelta(days=7)
            ticket = Ticket.objects.create(
                titulo=sorteio.choice(assuntos[categoria.nome]), descricao="Ticket do histórico de exemplo.",
                cliente=sorteio.choice(clientes), categoria=categoria, prioridade=prioridade, atendente=atendente,
                situacao=S.FECHADO if fechado else S.RESOLVIDO, aberto_em=aberto_em,
                resolvido_em=resolvido_em, fechado_em=resolvido_em + timedelta(days=7) if fechado else None,
            )
            assumido = aberto_em + timedelta(minutes=sorteio.randint(10, 90))
            Historico.objects.create(ticket=ticket, autor=atendente, campo="atendente", valor_novo=atendente.nome, alterado_em=assumido)
            Historico.objects.create(
                ticket=ticket, autor=atendente, campo="situacao", valor_anterior=S.ABERTO, valor_novo=S.EM_ATENDIMENTO,
                alterado_em=assumido,
            )
            Historico.objects.create(
                ticket=ticket, autor=atendente, campo="situacao", valor_anterior=S.EM_ATENDIMENTO, valor_novo=S.RESOLVIDO,
                alterado_em=resolvido_em,
            )
            if fechado:
                Historico.objects.create(
                    ticket=ticket, autor=atendente, campo="situacao", valor_anterior=S.RESOLVIDO, valor_novo=S.FECHADO,
                    alterado_em=ticket.fechado_em,
                )
            if sorteio.random() < 0.7:  # 70% dos clientes avaliam
                atraso = resolvido_em > ticket.prazo
                nota = sorteio.choices([1, 2, 3, 4, 5], weights=[2, 3, 3, 4, 2] if atraso else [0, 1, 2, 5, 8])[0]
                Avaliacao.objects.create(ticket=ticket, nota=nota, avaliado_em=resolvido_em + timedelta(hours=sorteio.uniform(1, 30)))
