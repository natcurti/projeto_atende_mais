from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from contas.models import Usuario

from . import services
from .models import Avaliacao, Categoria, Historico, Mensagem, Ticket
from .services import calcular_prazo


class CalcularPrazoTests(TestCase):
    """RN09: o prazo depende da prioridade."""

    def test_prazo_por_prioridade(self):
        aberto = timezone.now()
        self.assertEqual(calcular_prazo("urgente", aberto), aberto + timedelta(hours=4))
        self.assertEqual(calcular_prazo("alta", aberto), aberto + timedelta(days=1))
        self.assertEqual(calcular_prazo("media", aberto), aberto + timedelta(days=3))
        self.assertEqual(calcular_prazo("baixa", aberto), aberto + timedelta(days=5))

    def test_prioridade_desconhecida(self):
        with self.assertRaises(ValueError):
            calcular_prazo("altissima", timezone.now())


class TicketTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cliente = Usuario.objects.create_user("maria@exemplo.com", "senha-forte-123", nome="Maria", empresa="Souza ME")
        cls.atendente = Usuario.objects.create_user(
            "carlos@empresa.com", "senha-forte-123", nome="Carlos", perfil=Usuario.Perfil.ATENDENTE
        )
        cls.categoria = Categoria.objects.create(nome="Erro no sistema")

    def novo_ticket(self, **dados):
        dados.setdefault("titulo", "Erro ao emitir nota")
        dados.setdefault("descricao", "Aparece uma falha.")
        return Ticket.objects.create(cliente=self.cliente, categoria=self.categoria, **dados)

    def test_ticket_novo_nasce_aberto_sem_atendente_e_com_prazo(self):
        ticket = self.novo_ticket()
        self.assertEqual(ticket.situacao, Ticket.Situacao.ABERTO)  # RN03
        self.assertIsNone(ticket.atendente)
        self.assertEqual(ticket.prioridade, Ticket.Prioridade.MEDIA)
        self.assertEqual(ticket.prazo, ticket.aberto_em + timedelta(days=3))  # RN09

    def test_numeracao_comeca_em_1000(self):
        self.assertEqual(self.novo_ticket().pk, 1000)  # RN01
        self.assertEqual(self.novo_ticket().pk, 1001)

    def test_atrasado(self):
        ticket = self.novo_ticket(prioridade="urgente", aberto_em=timezone.now() - timedelta(hours=5))
        self.assertTrue(ticket.atrasado)  # RN10

    def test_aberto_com_atendente_e_recusado(self):
        with self.assertRaises(IntegrityError):
            self.novo_ticket(atendente=self.atendente)  # RN03

    def test_em_atendimento_sem_atendente_e_recusado(self):
        with self.assertRaises(IntegrityError):
            self.novo_ticket(situacao=Ticket.Situacao.EM_ATENDIMENTO)  # RN04

    def test_resolvido_sem_data_e_recusado(self):
        with self.assertRaises(IntegrityError):
            self.novo_ticket(situacao=Ticket.Situacao.RESOLVIDO, atendente=self.atendente)

    def test_mensagem_vazia_e_recusada(self):
        ticket = self.novo_ticket()
        with self.assertRaises(IntegrityError):
            Mensagem.objects.create(ticket=ticket, autor=self.cliente, texto="   ")

    def test_historico_sem_mudanca_e_recusado(self):
        ticket = self.novo_ticket()
        with self.assertRaises(IntegrityError):
            Historico.objects.create(
                ticket=ticket, autor=self.atendente, campo="situacao", valor_anterior="aberto", valor_novo="aberto"
            )

    def test_avaliacao_nota_entre_1_e_5_e_so_uma_por_ticket(self):
        ticket = self.novo_ticket(
            situacao=Ticket.Situacao.RESOLVIDO, atendente=self.atendente, resolvido_em=timezone.now()
        )
        with transaction.atomic(), self.assertRaises(IntegrityError):
            Avaliacao.objects.create(ticket=ticket, nota=6)  # RN11
        Avaliacao.objects.create(ticket=ticket, nota=5)
        with self.assertRaises(IntegrityError):
            Avaliacao.objects.create(ticket=ticket, nota=4)  # RN11


class DadosExemploTests(TestCase):
    def test_comando_carrega_os_dados_do_prototipo(self):
        call_command("carregar_dados_exemplo", stdout=StringIO())
        self.assertEqual(Usuario.objects.count(), 8)
        self.assertEqual(Ticket.objects.count(), 7)
        self.assertEqual(Ticket.objects.order_by("id").first().pk, 1000)
        urgente = Ticket.objects.get(prioridade="urgente")
        self.assertTrue(urgente.atrasado)


class PaginaInicialTests(TestCase):
    def test_raiz_leva_para_a_tela_de_entrada(self):
        resposta = self.client.get(reverse("inicio"), follow=True)
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Criar conta de cliente")


# ==========================================================
# F2: o cliente abre e acompanha tickets (RF06, RF07, RF09, RF12)
# ==========================================================

SENHA = "senha-forte-123"


class ClienteTestCase(TestCase):
    """Base: duas clientes, um atendente, categorias e um ticket da Maria em atendimento."""

    @classmethod
    def setUpTestData(cls):
        cls.maria = Usuario.objects.create_user("maria@exemplo.com", SENHA, nome="Maria Souza", empresa="Souza ME")
        cls.fernanda = Usuario.objects.create_user("fernanda@exemplo.com", SENHA, nome="Fernanda", empresa="Loja Central")
        cls.carlos = Usuario.objects.create_user("carlos@empresa.com", SENHA, nome="Carlos Lima", perfil=Usuario.Perfil.ATENDENTE)
        cls.erro = Categoria.objects.create(nome="Erro no sistema")
        cls.inativa = Categoria.objects.create(nome="Treinamento", ativa=False)
        cls.ticket = Ticket.objects.create(
            cliente=cls.maria, categoria=cls.erro, titulo="Erro ao emitir nota", descricao="Aparece uma falha.",
            situacao=Ticket.Situacao.EM_ATENDIMENTO, atendente=cls.carlos,
        )


class AbrirTicketTests(ClienteTestCase):
    def test_servico_abre_ticket_aberto_sem_atendente_e_com_prazo_medio(self):
        t = services.abrir_ticket(self.maria, "Sistema lento", "Demora 5 minutos.", self.erro)
        self.assertEqual((t.situacao, t.atendente, t.prioridade), ("aberto", None, "media"))  # RN03, RN09
        self.assertEqual(t.prazo - t.aberto_em, timedelta(days=3))
        self.assertGreaterEqual(t.pk, 1000)  # RN01

    def test_servico_recusa_categoria_inativa_e_quem_nao_e_cliente(self):
        with self.assertRaises(services.RegraDeNegocioError):
            services.abrir_ticket(self.maria, "T", "D", self.inativa)  # RN12
        with self.assertRaises(services.RegraDeNegocioError):
            services.abrir_ticket(self.carlos, "T", "D", self.erro)

    def test_tela_abre_ticket_e_volta_para_meus_tickets_com_aviso(self):
        self.client.force_login(self.maria)
        resposta = self.client.post(
            reverse("tickets:novo_ticket"),
            {"titulo": "Sistema lento", "categoria": self.erro.pk, "descricao": "Demora 5 minutos."},
            follow=True,
        )
        novo = Ticket.objects.get(titulo="Sistema lento")
        self.assertRedirects(resposta, reverse("tickets:meus_tickets"))
        self.assertContains(resposta, f"Ticket {novo.numero} enviado")
        self.assertEqual(novo.cliente, self.maria)

    def test_tela_nao_oferece_nem_aceita_categoria_inativa(self):
        self.client.force_login(self.maria)
        self.assertNotContains(self.client.get(reverse("tickets:novo_ticket")), "Treinamento")
        resposta = self.client.post(
            reverse("tickets:novo_ticket"), {"titulo": "T", "categoria": self.inativa.pk, "descricao": "D"}
        )
        self.assertTrue(resposta.context["form"].has_error("categoria"))

    def test_campos_obrigatorios(self):
        self.client.force_login(self.maria)
        resposta = self.client.post(reverse("tickets:novo_ticket"), {"titulo": "", "descricao": "   "})
        for campo in ("titulo", "categoria", "descricao"):
            self.assertTrue(resposta.context["form"].has_error(campo), campo)
        self.assertEqual(Ticket.objects.count(), 1)


class MeusTicketsTests(ClienteTestCase):
    def test_lista_so_os_tickets_da_cliente(self):  # RN08
        Ticket.objects.create(cliente=self.fernanda, categoria=self.erro, titulo="Ticket da Fernanda", descricao="D")
        self.client.force_login(self.maria)
        resposta = self.client.get(reverse("tickets:meus_tickets"))
        self.assertContains(resposta, "Erro ao emitir nota")
        self.assertNotContains(resposta, "Ticket da Fernanda")

    def test_filtro_por_situacao(self):
        Ticket.objects.create(cliente=self.maria, categoria=self.erro, titulo="Outro ticket aberto", descricao="D")
        self.client.force_login(self.maria)
        resposta = self.client.get(reverse("tickets:meus_tickets"), {"situacao": "aberto"})
        self.assertContains(resposta, "Outro ticket aberto")
        self.assertNotContains(resposta, "Erro ao emitir nota")

    def test_avisa_quantos_esperam_resposta(self):
        Ticket.objects.filter(pk=self.ticket.pk).update(situacao=Ticket.Situacao.AGUARDANDO_CLIENTE)
        self.client.force_login(self.maria)
        self.assertContains(self.client.get(reverse("tickets:meus_tickets")), "1 ticket espera uma resposta sua.")

    def test_cliente_sem_tickets_ve_convite_para_abrir(self):
        self.client.force_login(self.fernanda)
        self.assertContains(self.client.get(reverse("tickets:meus_tickets")), "Você ainda não abriu nenhum ticket")


class DetalheDoTicketClienteTests(ClienteTestCase):
    def url(self, ticket=None):
        return reverse("tickets:ticket_cliente", args=[(ticket or self.ticket).pk])

    def test_ticket_de_outra_cliente_nao_e_encontrado(self):  # RNF04, RN08
        self.client.force_login(self.fernanda)
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.assertEqual(self.client.post(self.url(), {"texto": "Invasão"}).status_code, 404)
        self.assertFalse(Mensagem.objects.filter(texto="Invasão").exists())

    def test_equipe_nao_usa_a_tela_do_cliente(self):
        self.client.force_login(self.carlos)
        self.assertEqual(self.client.get(self.url()).status_code, 403)

    def test_mostra_conversa_e_eventos_sem_notas_internas(self):  # RF09, RN08
        Mensagem.objects.create(ticket=self.ticket, autor=self.carlos, texto="Pode mandar um print?")
        Mensagem.objects.create(ticket=self.ticket, autor=self.carlos, texto="NOTA SECRETA DA EQUIPE", interna=True)
        Historico.objects.create(ticket=self.ticket, autor=self.carlos, campo="atendente", valor_novo="Carlos Lima")
        self.client.force_login(self.maria)
        resposta = self.client.get(self.url())
        self.assertContains(resposta, "Aparece uma falha.")  # descrição inicial
        self.assertContains(resposta, "Pode mandar um print?")
        self.assertContains(resposta, "Carlos Lima assumiu o atendimento")
        self.assertNotContains(resposta, "NOTA SECRETA DA EQUIPE")

    def test_responder_grava_mensagem_e_atualiza_o_ticket(self):  # RF12
        antes = self.ticket.atualizado_em
        self.client.force_login(self.maria)
        resposta = self.client.post(self.url(), {"texto": "Segue o print."}, follow=True)
        self.assertRedirects(resposta, self.url())
        self.assertContains(resposta, "Mensagem enviada.")
        self.assertTrue(Mensagem.objects.filter(ticket=self.ticket, autor=self.maria, texto="Segue o print.").exists())
        self.ticket.refresh_from_db()
        self.assertGreater(self.ticket.atualizado_em, antes)
        self.assertEqual(self.ticket.situacao, Ticket.Situacao.EM_ATENDIMENTO)

    def test_resposta_vazia_e_recusada(self):
        self.client.force_login(self.maria)
        resposta = self.client.post(self.url(), {"texto": "   "})
        self.assertContains(resposta, "Escreva a mensagem antes de enviar.")
        self.assertEqual(self.ticket.mensagens.count(), 0)

    def test_resposta_da_cliente_tira_de_aguardando_cliente(self):  # RN06, RN13
        Ticket.objects.filter(pk=self.ticket.pk).update(situacao=Ticket.Situacao.AGUARDANDO_CLIENTE)
        self.client.force_login(self.maria)
        self.client.post(self.url(), {"texto": "É do mês de outubro."})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.situacao, Ticket.Situacao.EM_ATENDIMENTO)
        evento = self.ticket.historico.get()
        self.assertEqual((evento.campo, evento.valor_anterior, evento.valor_novo, evento.autor),
                         ("situacao", "aguardando_cliente", "em_atendimento", self.maria))

    def test_ticket_resolvido_nao_recebe_resposta(self):
        resolvido = Ticket.objects.create(
            cliente=self.maria, categoria=self.erro, titulo="Já resolvido", descricao="D",
            situacao=Ticket.Situacao.RESOLVIDO, atendente=self.carlos, resolvido_em=timezone.now(),
        )
        self.client.force_login(self.maria)
        self.assertNotContains(self.client.get(self.url(resolvido)), "Enviar mensagem")
        resposta = self.client.post(self.url(resolvido), {"texto": "Oi?"}, follow=True)
        self.assertContains(resposta, "já foi resolvido")
        self.assertEqual(resolvido.mensagens.count(), 0)


class ServicoResponderTests(ClienteTestCase):
    def test_atendente_respondendo_nao_muda_a_situacao(self):
        Ticket.objects.filter(pk=self.ticket.pk).update(situacao=Ticket.Situacao.AGUARDANDO_CLIENTE)
        self.ticket.refresh_from_db()
        services.responder(self.ticket, self.carlos, "Mais alguma informação?")
        self.assertEqual(self.ticket.situacao, Ticket.Situacao.AGUARDANDO_CLIENTE)

    def test_cliente_nao_responde_ticket_alheio_nem_escreve_nota_interna(self):
        with self.assertRaises(services.RegraDeNegocioError):
            services.responder(self.ticket, self.fernanda, "Oi")
        with self.assertRaises(services.RegraDeNegocioError):
            services.responder(self.ticket, self.maria, "Oi", interna=True)

    def test_linha_do_tempo_em_ordem_e_com_notas_internas_so_para_a_equipe(self):
        agora = timezone.now()
        Mensagem.objects.create(ticket=self.ticket, autor=self.carlos, texto="nota", interna=True, criada_em=agora)
        Mensagem.objects.create(ticket=self.ticket, autor=self.maria, texto="depois", criada_em=agora + timedelta(minutes=1))
        cliente = [i.texto for i in services.linha_do_tempo(self.ticket, para_equipe=False)]
        equipe = [i.texto for i in services.linha_do_tempo(self.ticket, para_equipe=True)]
        self.assertEqual(cliente, ["Aparece uma falha.", "depois"])
        self.assertEqual(equipe, ["Aparece uma falha.", "nota", "depois"])


# ==========================================================
# F3: fila de atendimento (RF08, RN10)
# ==========================================================

class FilaTestCase(TestCase):
    """Base: equipe, clientes, categorias e tickets em situações e prazos variados."""

    @classmethod
    def setUpTestData(cls):
        cls.carlos = Usuario.objects.create_user("carlos@empresa.com", SENHA, nome="Carlos Lima", perfil=Usuario.Perfil.ATENDENTE)
        cls.ana = Usuario.objects.create_user("ana@empresa.com", SENHA, nome="Ana Reis", perfil=Usuario.Perfil.ATENDENTE)
        cls.maria = Usuario.objects.create_user("maria@exemplo.com", SENHA, nome="Maria", empresa="Souza ME")
        cls.erro = Categoria.objects.create(nome="Erro no sistema")
        cls.duvida = Categoria.objects.create(nome="Dúvida")
        agora = timezone.now()

        def novo(titulo, **dados):
            dados.setdefault("categoria", cls.erro)
            return Ticket.objects.create(cliente=cls.maria, titulo=titulo, descricao="D", **dados)

        # Prazos: média = 3 dias, urgente = 4 h, baixa = 5 dias (RN09)
        cls.atrasado = novo("Atrasado urgente", prioridade="urgente", aberto_em=agora - timedelta(hours=6))
        cls.aberto_duvida = novo("Dúvida aberta", categoria=cls.duvida, aberto_em=agora - timedelta(hours=1))
        cls.do_carlos = novo("Com o Carlos", situacao="em_atendimento", atendente=cls.carlos, aberto_em=agora - timedelta(days=1))
        cls.da_ana = novo("Com a Ana", prioridade="baixa", situacao="aguardando_cliente", atendente=cls.ana, aberto_em=agora)
        cls.resolvido = novo("Já resolvido", situacao="resolvido", atendente=cls.ana, resolvido_em=agora)

    def setUp(self):
        self.client.force_login(self.carlos)

    def titulos(self, **params):
        resposta = self.client.get(reverse("tickets:fila"), params)
        self.assertEqual(resposta.status_code, 200)
        return [t.titulo for t in resposta.context["pagina"].object_list]


class FilaTests(FilaTestCase):
    def test_mostra_so_tickets_em_aberto_atrasados_primeiro_e_depois_por_prazo(self):  # RF08, RN10
        self.assertEqual(self.titulos(), ["Atrasado urgente", "Com o Carlos", "Dúvida aberta", "Com a Ana"])

    def test_filtro_por_situacao_inclusive_resolvidos(self):
        self.assertEqual(self.titulos(situacao="em_atendimento"), ["Com o Carlos"])
        self.assertEqual(self.titulos(situacao="resolvido"), ["Já resolvido"])

    def test_filtro_por_categoria_e_prioridade(self):
        self.assertEqual(self.titulos(categoria=self.duvida.pk), ["Dúvida aberta"])
        self.assertEqual(self.titulos(prioridade="baixa"), ["Com a Ana"])

    def test_filtro_por_atendente_comigo_sem_e_pessoa(self):
        self.assertEqual(self.titulos(atendente="comigo"), ["Com o Carlos"])
        self.assertEqual(self.titulos(atendente="sem"), ["Atrasado urgente", "Dúvida aberta"])
        self.assertEqual(self.titulos(atendente=str(self.ana.pk)), ["Com a Ana"])

    def test_filtro_so_atrasados(self):
        self.assertEqual(self.titulos(atrasados="on"), ["Atrasado urgente"])

    def test_filtros_combinados(self):
        self.assertEqual(self.titulos(atendente="sem", categoria=self.erro.pk), ["Atrasado urgente"])
        self.assertEqual(self.titulos(atendente="sem", prioridade="baixa"), [])

    def test_valor_invalido_na_url_e_ignorado_sem_derrubar_os_outros_filtros(self):
        self.assertEqual(self.titulos(prioridade="altissima", atendente="comigo"), ["Com o Carlos"])
        self.assertEqual(len(self.titulos(categoria="abc")), 4)

    def test_contadores(self):
        resposta = self.client.get(reverse("tickets:fila"))
        self.assertEqual(
            resposta.context["contadores"],
            {"abertos": 2, "em_atendimento": 1, "aguardando_cliente": 1, "atrasados": 1},
        )

    def test_linha_atrasada_em_destaque(self):
        resposta = self.client.get(reverse("tickets:fila"))
        self.assertContains(resposta, 'class="linha-atrasada"', count=1)
        self.assertContains(resposta, "Atrasado há 2\xa0horas")  # \xa0: espaço que não quebra a linha

    def test_paginacao_mantem_os_filtros(self):
        for i in range(25):
            Ticket.objects.create(cliente=self.maria, categoria=self.duvida, titulo=f"Lote {i}", descricao="D")
        primeira = self.client.get(reverse("tickets:fila"), {"categoria": self.duvida.pk})
        self.assertEqual(primeira.context["pagina"].paginator.count, 26)
        self.assertEqual(len(primeira.context["pagina"].object_list), 20)
        self.assertContains(primeira, f"categoria={self.duvida.pk}&amp;pagina=2")
        segunda = self.client.get(reverse("tickets:fila"), {"categoria": self.duvida.pk, "pagina": 2})
        self.assertEqual(len(segunda.context["pagina"].object_list), 6)

    def test_numero_de_consultas_nao_cresce_com_a_fila(self):  # RNF07
        def consultas():
            from django.db import connection
            from django.test.utils import CaptureQueriesContext

            with CaptureQueriesContext(connection) as ctx:
                self.client.get(reverse("tickets:fila"))
            return len(ctx.captured_queries)

        antes = consultas()
        for i in range(15):
            Ticket.objects.create(cliente=self.maria, categoria=self.erro, titulo=f"Mais {i}", descricao="D")
        self.assertEqual(consultas(), antes)

    def test_cliente_nao_acessa_a_fila(self):
        self.client.force_login(self.maria)
        self.assertEqual(self.client.get(reverse("tickets:fila")).status_code, 403)


# ==========================================================
# F4: atender o ticket (RF09, RF10, RF11, RF12, RN04, RN05, RN13)
# ==========================================================

class AtendimentoTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.carlos = Usuario.objects.create_user("carlos@empresa.com", SENHA, nome="Carlos Lima", perfil=Usuario.Perfil.ATENDENTE)
        cls.ana = Usuario.objects.create_user("ana@empresa.com", SENHA, nome="Ana Reis", perfil=Usuario.Perfil.ATENDENTE)
        cls.juliana = Usuario.objects.create_user("juliana@empresa.com", SENHA, nome="Juliana Prado", perfil=Usuario.Perfil.ADMINISTRADOR)
        cls.pedro = Usuario.objects.create_user(
            "pedro@empresa.com", SENHA, nome="Pedro Alves", perfil=Usuario.Perfil.ATENDENTE, is_active=False
        )
        cls.maria = Usuario.objects.create_user("maria@exemplo.com", SENHA, nome="Maria Souza", empresa="Souza ME")
        cls.erro = Categoria.objects.create(nome="Erro no sistema")

    def setUp(self):
        self.aberto = Ticket.objects.create(cliente=self.maria, categoria=self.erro, titulo="Erro na nota", descricao="Falha.")

    def com_carlos(self):
        services.assumir(self.aberto, self.carlos)
        return self.aberto


class AssumirEAtribuirTests(AtendimentoTestCase):
    def test_assumir_coloca_o_ticket_com_o_atendente_e_registra_no_historico(self):  # RF10, RN04, RN13
        services.assumir(self.aberto, self.carlos)
        self.aberto.refresh_from_db()
        self.assertEqual((self.aberto.atendente, self.aberto.situacao), (self.carlos, "em_atendimento"))
        eventos = [(h.campo, h.valor_anterior, h.valor_novo) for h in self.aberto.historico.all()]
        self.assertEqual(eventos, [("atendente", None, "Carlos Lima"), ("situacao", "aberto", "em_atendimento")])

    def test_nao_assume_ticket_que_ja_tem_atendente(self):
        self.com_carlos()
        with self.assertRaisesMessage(services.RegraDeNegocioError, "já está com Carlos Lima"):
            services.assumir(self.aberto, self.ana)

    def test_cliente_nao_assume(self):
        with self.assertRaises(services.RegraDeNegocioError):
            services.assumir(self.aberto, self.maria)

    def test_administrador_passa_ticket_aberto_para_alguem(self):  # RF10
        services.atribuir(self.aberto, self.juliana, self.ana)
        self.aberto.refresh_from_db()
        self.assertEqual((self.aberto.atendente, self.aberto.situacao), (self.ana, "em_atendimento"))
        self.assertEqual(self.aberto.historico.first().descricao, "Juliana Prado passou o atendimento para Ana Reis")

    def test_administrador_troca_o_atendente(self):
        self.com_carlos()
        services.atribuir(self.aberto, self.juliana, self.ana)
        evento = self.aberto.historico.filter(campo="atendente").last()
        self.assertEqual((evento.valor_anterior, evento.valor_novo), ("Carlos Lima", "Ana Reis"))

    def test_so_administrador_atribui_e_so_para_equipe_ativa(self):
        with self.assertRaises(services.RegraDeNegocioError):
            services.atribuir(self.aberto, self.carlos, self.ana)
        with self.assertRaises(services.RegraDeNegocioError):
            services.atribuir(self.aberto, self.juliana, self.pedro)  # desativado
        with self.assertRaises(services.RegraDeNegocioError):
            services.atribuir(self.aberto, self.juliana, self.maria)  # cliente


class MudarSituacaoTests(AtendimentoTestCase):
    def test_responsavel_pede_informacao_e_resolve(self):  # RF11
        self.com_carlos()
        services.mudar_situacao(self.aberto, self.carlos, "aguardando_cliente")
        self.assertEqual(self.aberto.situacao, "aguardando_cliente")
        services.mudar_situacao(self.aberto, self.carlos, "resolvido")
        self.aberto.refresh_from_db()
        self.assertEqual(self.aberto.situacao, "resolvido")
        self.assertIsNotNone(self.aberto.resolvido_em)

    def test_outro_atendente_nao_muda_a_situacao(self):  # RN05
        self.com_carlos()
        with self.assertRaisesMessage(services.RegraDeNegocioError, "está com Carlos Lima"):
            services.mudar_situacao(self.aberto, self.ana, "resolvido")

    def test_administrador_muda_a_situacao_de_qualquer_ticket(self):  # RN05
        self.com_carlos()
        services.mudar_situacao(self.aberto, self.juliana, "resolvido")
        self.assertEqual(self.aberto.situacao, "resolvido")

    def test_ticket_aberto_precisa_ser_assumido_antes(self):
        with self.assertRaisesMessage(services.RegraDeNegocioError, "Assuma o ticket"):
            services.mudar_situacao(self.aberto, self.juliana, "resolvido")

    def test_transicoes_nao_permitidas(self):
        self.com_carlos()
        with self.assertRaises(services.RegraDeNegocioError):
            services.mudar_situacao(self.aberto, self.carlos, "aberto")
        with self.assertRaises(services.RegraDeNegocioError):
            services.mudar_situacao(self.aberto, self.carlos, "fechado")
        services.mudar_situacao(self.aberto, self.carlos, "resolvido")
        with self.assertRaises(services.RegraDeNegocioError):
            services.mudar_situacao(self.aberto, self.carlos, "em_atendimento")  # reabrir é RF15, depois do MVP

    def test_equipe_so_responde_quando_pode_atuar(self):  # RN05
        with self.assertRaisesMessage(services.RegraDeNegocioError, "Assuma o ticket"):
            services.responder(self.aberto, self.carlos, "Oi")
        self.com_carlos()
        with self.assertRaises(services.RegraDeNegocioError):
            services.responder(self.aberto, self.ana, "Oi")
        services.responder(self.aberto, self.juliana, "Oi, sou a coordenadora.")


class TelaDeAtendimentoTests(AtendimentoTestCase):
    def url(self, nome="tickets:ticket_equipe"):
        return reverse(nome, args=[self.aberto.pk])

    def test_cliente_nao_acessa_e_numero_inexistente_da_404(self):
        self.client.force_login(self.maria)
        self.assertEqual(self.client.get(self.url()).status_code, 403)
        self.client.force_login(self.carlos)
        self.assertEqual(self.client.get(reverse("tickets:ticket_equipe", args=[999999])).status_code, 404)

    def test_equipe_ve_as_notas_internas(self):  # RF09
        self.com_carlos()
        Mensagem.objects.create(ticket=self.aberto, autor=self.carlos, texto="Verificar certificado.", interna=True)
        self.client.force_login(self.ana)
        resposta = self.client.get(self.url())
        self.assertContains(resposta, "Verificar certificado.")
        self.assertContains(resposta, "Nota interna")

    def test_ticket_aberto_mostra_assumir_e_so_permite_nota_interna(self):
        self.client.force_login(self.carlos)
        resposta = self.client.get(self.url())
        self.assertContains(resposta, "Assumir ticket")
        self.assertEqual(resposta.context["form"].fields["tipo"].choices, [("interna", "Nota interna")])

    def test_assumir_pela_fila_leva_para_o_ticket(self):
        self.client.force_login(self.carlos)
        resposta = self.client.post(self.url("tickets:assumir"), follow=True)
        self.assertRedirects(resposta, self.url())
        self.assertContains(resposta, f"Ticket {self.aberto.numero} assumido")
        self.assertContains(resposta, "Mensagem ao cliente")

    def test_assumir_so_por_post(self):
        self.client.force_login(self.carlos)
        self.assertEqual(self.client.get(self.url("tickets:assumir")).status_code, 405)

    def test_outro_atendente_ve_o_motivo_e_nao_gerencia(self):
        self.com_carlos()
        self.client.force_login(self.ana)
        resposta = self.client.get(self.url())
        self.assertContains(resposta, "Este ticket está com Carlos Lima")
        self.assertNotContains(resposta, "Gerenciar ticket")
        self.client.post(self.url("tickets:gerenciar"), {"situacao": "resolvido"})
        self.aberto.refresh_from_db()
        self.assertEqual(self.aberto.situacao, "em_atendimento")

    def test_responsavel_muda_a_situacao_pelo_painel(self):
        self.com_carlos()
        self.client.force_login(self.carlos)
        resposta = self.client.post(self.url("tickets:gerenciar"), {"situacao": "aguardando_cliente"}, follow=True)
        self.assertContains(resposta, "situação alterada para Aguardando cliente")
        self.assertContains(resposta, "Situação alterada de Em atendimento para Aguardando cliente")

    def test_administrador_passa_ticket_aberto_pelo_painel(self):
        self.client.force_login(self.juliana)
        self.assertContains(self.client.get(self.url()), "Ninguém ainda")
        resposta = self.client.post(
            self.url("tickets:gerenciar"), {"atendente": self.ana.pk, "situacao": "aberto"}, follow=True
        )
        self.assertContains(resposta, "ticket passado para Ana Reis")
        self.aberto.refresh_from_db()
        self.assertEqual((self.aberto.atendente, self.aberto.situacao), (self.ana, "em_atendimento"))

    def test_fila_tem_links_e_botao_assumir(self):
        self.client.force_login(self.carlos)
        resposta = self.client.get(reverse("tickets:fila"))
        self.assertContains(resposta, f'href="{self.url()}"')
        self.assertContains(resposta, f'action="{self.url("tickets:assumir")}"')


class CicloCompletoTests(AtendimentoTestCase):
    """O roteiro de demonstração do Checkpoint 2, de ponta a ponta, pelas telas."""

    def test_ciclo_do_ticket(self):
        # 1. Maria abre o ticket
        self.client.force_login(self.maria)
        self.client.post(reverse("tickets:novo_ticket"), {"titulo": "Sistema lento", "categoria": self.erro.pk, "descricao": "Demora."})
        ticket = Ticket.objects.get(titulo="Sistema lento")
        url_equipe = reverse("tickets:ticket_equipe", args=[ticket.pk])
        url_cliente = reverse("tickets:ticket_cliente", args=[ticket.pk])

        # 2. Carlos assume pela fila e pede mais informação
        self.client.force_login(self.carlos)
        self.client.post(reverse("tickets:assumir", args=[ticket.pk]))
        self.client.post(url_equipe, {"texto": "Qual relatório está lento?"})
        self.client.post(reverse("tickets:gerenciar", args=[ticket.pk]), {"situacao": "aguardando_cliente"})

        # 3. Maria responde e o ticket volta para Em atendimento sozinho (RN06)
        self.client.force_login(self.maria)
        self.assertContains(self.client.get(url_cliente), "Qual relatório está lento?")
        self.client.post(url_cliente, {"texto": "O de vendas."})
        ticket.refresh_from_db()
        self.assertEqual(ticket.situacao, "em_atendimento")

        # 4. Carlos resolve
        self.client.force_login(self.carlos)
        self.client.post(reverse("tickets:gerenciar", args=[ticket.pk]), {"situacao": "resolvido"})

        # 5. Maria vê o ticket resolvido, com todo o histórico, e não pode mais responder
        self.client.force_login(self.maria)
        resposta = self.client.get(url_cliente)
        self.assertContains(resposta, "Resolvido")
        self.assertContains(resposta, "Carlos Lima assumiu o atendimento")
        self.assertContains(resposta, "Carlos Lima marcou o ticket como resolvido")
        self.assertNotContains(resposta, "Enviar mensagem")
        self.assertEqual(ticket.historico.count(), 5)


# ==========================================================
# F5: administração das categorias (RF05, RN12)
# ==========================================================

class AdministracaoCategoriasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.juliana = Usuario.objects.create_user("juliana@empresa.com", SENHA, nome="Juliana", perfil=Usuario.Perfil.ADMINISTRADOR)
        cls.carlos = Usuario.objects.create_user("carlos@empresa.com", SENHA, nome="Carlos", perfil=Usuario.Perfil.ATENDENTE)
        cls.maria = Usuario.objects.create_user("maria@exemplo.com", SENHA, nome="Maria", empresa="Souza ME")
        cls.duvida = Categoria.objects.create(nome="Dúvida")

    def setUp(self):
        self.client.force_login(self.juliana)

    def test_so_administrador(self):
        self.client.force_login(self.carlos)
        self.assertEqual(self.client.post(reverse("tickets:nova_categoria"), {"nome": "X"}).status_code, 403)
        self.assertEqual(self.client.get(reverse("tickets:editar_categoria", args=[self.duvida.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("tickets:alterar_categoria", args=[self.duvida.pk])).status_code, 403)

    def test_cria_categoria_que_ja_aparece_para_o_cliente(self):  # RF05
        resposta = self.client.post(reverse("tickets:nova_categoria"), {"nome": "  Integrações   fiscais "}, follow=True)
        self.assertContains(resposta, "Categoria Integrações fiscais criada")
        self.client.force_login(self.maria)
        self.assertContains(self.client.get(reverse("tickets:novo_ticket")), "Integrações fiscais")

    def test_nome_repetido_com_outras_maiusculas_e_recusado(self):
        resposta = self.client.post(reverse("tickets:nova_categoria"), {"nome": "DÚVIDA"}, follow=True)
        self.assertContains(resposta, "Já existe uma categoria com este nome.")
        self.assertEqual(Categoria.objects.count(), 1)

    def test_renomear_muda_o_nome_nos_tickets_antigos(self):
        ticket = Ticket.objects.create(cliente=self.maria, categoria=self.duvida, titulo="T", descricao="D")
        self.client.post(reverse("tickets:editar_categoria", args=[self.duvida.pk]), {"nome": "Dúvidas gerais"})
        self.client.force_login(self.maria)
        self.assertContains(self.client.get(reverse("tickets:ticket_cliente", args=[ticket.pk])), "Dúvidas gerais")

    def test_desativar_some_da_abertura_mas_fica_nos_tickets_antigos(self):  # RN12
        ticket = Ticket.objects.create(cliente=self.maria, categoria=self.duvida, titulo="T", descricao="D")
        self.client.post(reverse("tickets:alterar_categoria", args=[self.duvida.pk]))
        self.duvida.refresh_from_db()
        self.assertFalse(self.duvida.ativa)
        self.client.force_login(self.maria)
        opcoes = self.client.get(reverse("tickets:novo_ticket")).context["form"].fields["categoria"].queryset
        self.assertNotIn(self.duvida, opcoes)
        self.assertContains(self.client.get(reverse("tickets:ticket_cliente", args=[ticket.pk])), "Dúvida")
        self.client.force_login(self.juliana)
        self.client.post(reverse("tickets:alterar_categoria", args=[self.duvida.pk]))
        self.duvida.refresh_from_db()
        self.assertTrue(self.duvida.ativa)


# ==========================================================
# Evolução (v0.2.0) — E1: notas internas (RF13)
# ==========================================================

class NotasInternasTests(AtendimentoTestCase):
    def url(self):
        return reverse("tickets:ticket_equipe", args=[self.aberto.pk])

    def test_responsavel_escreve_nota_e_o_cliente_nao_ve(self):  # RF13, RN08
        self.com_carlos()
        self.client.force_login(self.carlos)
        resposta = self.client.post(self.url(), {"tipo": "interna", "texto": "Cliente usa a versão antiga."}, follow=True)
        self.assertContains(resposta, "Nota interna salva.")
        nota = self.aberto.mensagens.get()
        self.assertTrue(nota.interna)
        self.client.force_login(self.maria)
        cliente = self.client.get(reverse("tickets:ticket_cliente", args=[self.aberto.pk]))
        self.assertNotContains(cliente, "Cliente usa a versão antiga.")

    def test_nota_nao_muda_a_ultima_atualizacao_vista_pelo_cliente(self):
        self.com_carlos()
        antes = Ticket.objects.get(pk=self.aberto.pk).atualizado_em
        services.responder(self.aberto, self.carlos, "Anotação", interna=True)
        self.assertEqual(Ticket.objects.get(pk=self.aberto.pk).atualizado_em, antes)

    def test_outro_atendente_deixa_nota_mas_nao_responde_ao_cliente(self):  # RN05
        self.com_carlos()
        services.responder(self.aberto, self.ana, "Já vi esse erro antes, fala comigo.", interna=True)
        with self.assertRaises(services.RegraDeNegocioError):
            services.responder(self.aberto, self.ana, "Oi, Maria", interna=False)
        self.client.force_login(self.ana)
        self.client.post(self.url(), {"tipo": "cliente", "texto": "Tentando responder ao cliente"})
        self.assertFalse(self.aberto.mensagens.filter(texto="Tentando responder ao cliente").exists())

    def test_ticket_aberto_aceita_nota_antes_de_ser_assumido(self):
        self.client.force_login(self.ana)
        self.client.post(self.url(), {"texto": "Parece urgente, alguém pega?"})  # sem tipo: só pode ser nota
        nota = self.aberto.mensagens.get()
        self.assertTrue(nota.interna)
        self.aberto.refresh_from_db()
        self.assertEqual(self.aberto.situacao, "aberto")

    def test_tipo_padrao_do_responsavel_e_mensagem_ao_cliente(self):
        self.com_carlos()
        self.client.force_login(self.carlos)
        self.client.post(self.url(), {"texto": "Olá, Maria!"})
        self.assertFalse(self.aberto.mensagens.get().interna)


# ==========================================================
# Evolução (v0.2.0) — E2: mudar a prioridade (RF17, RN09)
# ==========================================================

class PrioridadeTests(AtendimentoTestCase):
    def gerenciar(self, **dados):
        return self.client.post(reverse("tickets:gerenciar", args=[self.aberto.pk]), dados, follow=True)

    def test_responsavel_muda_a_prioridade_e_o_prazo_e_recalculado(self):  # RF17, RN09
        self.com_carlos()
        services.mudar_prioridade(self.aberto, self.carlos, "urgente")
        self.aberto.refresh_from_db()
        self.assertEqual(self.aberto.prioridade, "urgente")
        self.assertEqual(self.aberto.prazo, self.aberto.aberto_em + timedelta(hours=4))
        evento = self.aberto.historico.get(campo="prioridade")
        self.assertEqual(evento.descricao, "Prioridade alterada de Média para Urgente")

    def test_mudar_para_urgente_um_ticket_antigo_o_deixa_atrasado(self):  # RN10
        Ticket.objects.filter(pk=self.aberto.pk).update(aberto_em=timezone.now() - timedelta(hours=6))
        self.aberto.refresh_from_db()
        services.mudar_prioridade(self.aberto, self.juliana, "urgente")
        self.assertTrue(self.aberto.atrasado)

    def test_outro_atendente_nao_muda(self):  # RN05
        self.com_carlos()
        with self.assertRaises(services.RegraDeNegocioError):
            services.mudar_prioridade(self.aberto, self.ana, "alta")

    def test_administrador_tria_ticket_ainda_aberto(self):
        services.mudar_prioridade(self.aberto, self.juliana, "alta")
        self.aberto.refresh_from_db()
        self.assertEqual((self.aberto.prioridade, self.aberto.situacao), ("alta", "aberto"))

    def test_atendente_nao_tria_ticket_aberto_sem_assumir(self):
        with self.assertRaisesMessage(services.RegraDeNegocioError, "Assuma o ticket"):
            services.mudar_prioridade(self.aberto, self.carlos, "alta")

    def test_ticket_resolvido_nao_muda_de_prioridade(self):
        self.com_carlos()
        services.mudar_situacao(self.aberto, self.carlos, "resolvido")
        with self.assertRaises(services.RegraDeNegocioError):
            services.mudar_prioridade(self.aberto, self.carlos, "baixa")

    def test_pelo_painel_mostra_o_novo_prazo(self):
        self.com_carlos()
        self.client.force_login(self.carlos)
        resposta = self.gerenciar(situacao="em_atendimento", prioridade="baixa")
        self.assertContains(resposta, "prioridade alterada para Baixa, com novo prazo em")
        self.assertContains(resposta, "Prioridade alterada de Média para Baixa")

    def test_pelo_painel_muda_prioridade_e_resolve_juntos(self):
        self.com_carlos()
        self.client.force_login(self.carlos)
        self.gerenciar(situacao="resolvido", prioridade="alta")
        self.aberto.refresh_from_db()
        self.assertEqual((self.aberto.prioridade, self.aberto.situacao), ("alta", "resolvido"))
