from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from contas.models import Usuario
from tickets.models import Avaliacao, Categoria, Ticket

from . import services

SENHA = "senha-forte-123"


class PainelTests(TestCase):
    """RF18: indicadores do atendimento para o administrador."""

    @classmethod
    def setUpTestData(cls):
        cls.juliana = Usuario.objects.create_user("juliana@empresa.com", SENHA, nome="Juliana", perfil=Usuario.Perfil.ADMINISTRADOR)
        cls.carlos = Usuario.objects.create_user("carlos@empresa.com", SENHA, nome="Carlos", perfil=Usuario.Perfil.ATENDENTE)
        cls.ana = Usuario.objects.create_user("ana@empresa.com", SENHA, nome="Ana", perfil=Usuario.Perfil.ATENDENTE)
        cls.maria = Usuario.objects.create_user("maria@exemplo.com", SENHA, nome="Maria", empresa="Souza ME")
        cls.erro = Categoria.objects.create(nome="Erro no sistema")
        cls.duvida = Categoria.objects.create(nome="Dúvida")
        agora = timezone.now()

        def resolvido(categoria, atendente, aberto_ha_dias, horas, nota=None):
            aberto = agora - timedelta(days=aberto_ha_dias)
            t = Ticket.objects.create(
                cliente=cls.maria, categoria=categoria, titulo="T", descricao="D", atendente=atendente,
                situacao="resolvido", aberto_em=aberto, resolvido_em=aberto + timedelta(hours=horas),
            )
            if nota:
                Avaliacao.objects.create(ticket=t, nota=nota, avaliado_em=t.resolvido_em)
            return t

        # Prazo de prioridade média = 72 h: o de 80 h ficou fora do prazo.
        resolvido(cls.erro, cls.carlos, 5, 10, nota=5)
        resolvido(cls.erro, cls.carlos, 10, 80, nota=2)
        resolvido(cls.duvida, cls.ana, 3, 3, nota=4)
        resolvido(cls.duvida, cls.ana, 60, 6)  # fora dos últimos 30 dias
        Ticket.objects.create(cliente=cls.maria, categoria=cls.duvida, titulo="Aberto", descricao="D", aberto_em=agora - timedelta(days=1))
        Ticket.objects.create(  # urgente aberto há 6 h: atrasado
            cliente=cls.maria, categoria=cls.erro, titulo="Urgente", descricao="D", prioridade="urgente",
            situacao="em_atendimento", atendente=cls.carlos, aberto_em=agora - timedelta(hours=6),
        )

    def test_indicadores_dos_ultimos_30_dias(self):
        ind = services.calcular(30)
        self.assertEqual((ind.em_aberto, ind.atrasados), (2, 1))
        self.assertEqual((ind.abertos_no_periodo, ind.resolvidos_no_periodo), (5, 3))
        self.assertEqual(ind.tempo_medio_horas, 31.0)  # (10 + 80 + 3) / 3
        self.assertEqual(ind.no_prazo_percentual, 67)  # 2 de 3
        self.assertEqual((ind.nota_media, ind.avaliacoes), (3.7, 3))  # (5 + 2 + 4) / 3

    def test_periodo_maior_inclui_os_mais_antigos(self):
        self.assertEqual(services.calcular(90).resolvidos_no_periodo, 4)
        self.assertEqual(services.calcular(7).resolvidos_no_periodo, 3)  # o de 10 dias levou 80 h: resolvido há 6,7 dias

    def test_abertos_por_dia_tem_todos_os_dias_do_periodo(self):
        ind = services.calcular(7)
        self.assertEqual(len(ind.abertos_por_dia), 7)
        self.assertEqual(sum(d["quantidade"] for d in ind.abertos_por_dia), ind.abertos_no_periodo)
        self.assertEqual(ind.abertos_por_dia[-1]["dia"], timezone.localdate())

    def test_por_categoria_e_por_atendente(self):
        ind = services.calcular(30)
        erro = next(c for c in ind.por_categoria if c["nome"] == "Erro no sistema")
        self.assertEqual((erro["abertos"], erro["resolvidos"], erro["tempo_medio_horas"]), (3, 2, 45.0))
        carlos = next(a for a in ind.por_atendente if a["nome"] == "Carlos")
        self.assertEqual(
            (carlos["resolvidos"], carlos["em_aberto"], carlos["atrasados"], carlos["no_prazo_percentual"], carlos["nota_media"]),
            (2, 1, 1, 50, 3.5),
        )

    def test_sem_dados_nao_quebra(self):
        Avaliacao.objects.all().delete()
        Ticket.objects.all().delete()
        ind = services.calcular(30)
        self.assertEqual((ind.resolvidos_no_periodo, ind.tempo_medio_horas, ind.nota_media), (0, None, None))
        self.client.force_login(self.juliana)
        self.assertContains(self.client.get(reverse("painel:painel")), "Nenhum ticket aberto neste período.")

    def test_tela_so_para_administrador(self):
        for usuario in (self.carlos, self.maria):
            self.client.force_login(usuario)
            self.assertEqual(self.client.get(reverse("painel:painel")).status_code, 403)
        self.client.force_login(self.juliana)
        resposta = self.client.get(reverse("painel:painel"))
        self.assertContains(resposta, "Painel de indicadores")
        self.assertContains(resposta, "31,0 h")  # tempo médio, com vírgula
        self.assertContains(resposta, "67% dentro do prazo")

    def test_periodo_invalido_volta_para_30_dias(self):
        self.client.force_login(self.juliana)
        for valor in ("15", "abc", "-1"):
            self.assertEqual(self.client.get(reverse("painel:painel"), {"dias": valor}).context["ind"].dias, 30)

    def test_menu_mostra_painel_so_para_administrador(self):
        self.client.force_login(self.juliana)
        self.assertContains(self.client.get(reverse("tickets:fila")), 'href="/painel/"')
        self.client.force_login(self.carlos)
        self.assertNotContains(self.client.get(reverse("tickets:fila")), 'href="/painel/"')
