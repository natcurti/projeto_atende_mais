from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from contas.models import Usuario

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
