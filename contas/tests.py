from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import Usuario


class CriacaoDeUsuarioTests(TestCase):
    def test_cliente_entra_pelo_email_e_senha_vira_hash(self):
        usuario = Usuario.objects.create_user(
            "Maria@Exemplo.com", "senha-forte-123", nome="Maria", empresa="Souza ME"
        )
        self.assertEqual(usuario.email, "maria@exemplo.com")  # e-mail sempre em minúsculas
        self.assertEqual(usuario.perfil, Usuario.Perfil.CLIENTE)
        self.assertNotEqual(usuario.password, "senha-forte-123")  # RNF03
        self.assertTrue(usuario.check_password("senha-forte-123"))

    def test_cliente_sem_empresa_e_recusado(self):
        with self.assertRaises(ValueError):
            Usuario.objects.create_user("x@exemplo.com", "senha-forte-123", nome="X")

    def test_banco_recusa_cliente_sem_empresa(self):
        # Mesmo sem passar pelo create_user, o banco impede (ck_usuario_empresa).
        with self.assertRaises(IntegrityError):
            Usuario.objects.create(email="y@exemplo.com", nome="Y", perfil=Usuario.Perfil.CLIENTE)

    def test_atendente_nao_precisa_de_empresa(self):
        atendente = Usuario.objects.create_user(
            "carlos@empresa.com", "senha-forte-123", nome="Carlos", perfil=Usuario.Perfil.ATENDENTE
        )
        self.assertTrue(atendente.eh_equipe)
        self.assertFalse(atendente.is_staff)

    def test_superusuario_e_administrador(self):
        admin = Usuario.objects.create_superuser("juliana@empresa.com", "senha-forte-123", nome="Juliana")
        self.assertEqual(admin.perfil, Usuario.Perfil.ADMINISTRADOR)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)

    def test_email_nao_se_repete(self):
        Usuario.objects.create_user("a@empresa.com", "senha-forte-123", nome="A", perfil=Usuario.Perfil.ATENDENTE)
        with self.assertRaises(IntegrityError):
            Usuario.objects.create_user("a@empresa.com", "senha-forte-123", nome="B", perfil=Usuario.Perfil.ATENDENTE)


SENHA = "senha-forte-123"


class AcessoTestCase(TestCase):
    """Base com um usuário de cada perfil."""

    @classmethod
    def setUpTestData(cls):
        cls.cliente = Usuario.objects.create_user("maria@exemplo.com", SENHA, nome="Maria", empresa="Souza ME")
        cls.atendente = Usuario.objects.create_user(
            "carlos@empresa.com", SENHA, nome="Carlos", perfil=Usuario.Perfil.ATENDENTE
        )
        cls.admin = Usuario.objects.create_user(
            "juliana@empresa.com", SENHA, nome="Juliana", perfil=Usuario.Perfil.ADMINISTRADOR
        )

    def entrar(self, email, senha=SENHA, **extra):
        return self.client.post(reverse("contas:entrada"), {"acao": "entrar", "username": email, "password": senha, **extra})


class CadastroViewTests(AcessoTestCase):
    """RF01: cadastro de cliente."""

    def dados(self, **mudancas):
        dados = {
            "acao": "cadastrar", "nome": "Fernanda Lopes", "email": "Fernanda@LojaCentral.com.br",
            "empresa": "Loja Central", "senha": "Atende#Seguro9", "senha_confirmacao": "Atende#Seguro9",
        }
        dados.update(mudancas)
        return dados

    def test_cadastro_cria_cliente_e_ja_entra(self):
        resposta = self.client.post(reverse("contas:entrada"), self.dados())
        self.assertRedirects(resposta, reverse("tickets:meus_tickets"))
        usuario = Usuario.objects.get(email="fernanda@lojacentral.com.br")
        self.assertEqual(usuario.perfil, Usuario.Perfil.CLIENTE)
        self.assertEqual(int(self.client.session["_auth_user_id"]), usuario.pk)

    def test_email_ja_cadastrado_com_outras_maiusculas(self):
        resposta = self.client.post(reverse("contas:entrada"), self.dados(email="MARIA@exemplo.com"))
        self.assertContains(resposta, "Já existe uma conta com este e-mail")
        self.assertEqual(Usuario.objects.filter(email="maria@exemplo.com").count(), 1)

    def test_empresa_obrigatoria(self):
        resposta = self.client.post(reverse("contas:entrada"), self.dados(empresa=""))
        self.assertFalse(Usuario.objects.filter(email="fernanda@lojacentral.com.br").exists())
        self.assertTrue(resposta.context["form_cadastro"].has_error("empresa"))

    def test_senhas_diferentes(self):
        resposta = self.client.post(reverse("contas:entrada"), self.dados(senha_confirmacao="Outra#Senha9"))
        self.assertContains(resposta, "As senhas não são iguais.")

    def test_senha_curta_e_recusada(self):
        resposta = self.client.post(reverse("contas:entrada"), self.dados(senha="Ab#1", senha_confirmacao="Ab#1"))
        self.assertTrue(resposta.context["form_cadastro"].has_error("senha"))
        self.assertFalse(Usuario.objects.filter(email="fernanda@lojacentral.com.br").exists())


class EntrarSairTests(AcessoTestCase):
    """RF02: entrar e sair, com cada perfil indo para a sua tela."""

    def test_cliente_vai_para_meus_tickets(self):
        self.assertRedirects(self.entrar("maria@exemplo.com"), reverse("tickets:meus_tickets"))

    def test_atendente_e_administrador_vao_para_a_fila(self):
        self.assertRedirects(self.entrar("carlos@empresa.com"), reverse("tickets:fila"))
        self.client.post(reverse("contas:sair"))
        self.assertRedirects(self.entrar("juliana@empresa.com"), reverse("tickets:fila"))

    def test_email_com_maiusculas_funciona(self):
        self.assertRedirects(self.entrar("  Maria@Exemplo.COM "), reverse("tickets:meus_tickets"))

    def test_senha_errada(self):
        resposta = self.entrar("maria@exemplo.com", "senha-errada")
        self.assertContains(resposta, "E-mail ou senha incorretos")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_usuario_desativado_nao_entra(self):
        Usuario.objects.filter(pk=self.atendente.pk).update(is_active=False)  # RN12
        resposta = self.entrar("carlos@empresa.com")
        self.assertEqual(resposta.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_volta_para_a_pagina_pedida_antes_do_login(self):
        self.assertRedirects(self.entrar("carlos@empresa.com", next="/fila/"), "/fila/")

    def test_ignora_endereco_externo_no_next(self):
        resposta = self.entrar("carlos@empresa.com", next="https://site-malicioso.com/")
        self.assertRedirects(resposta, reverse("tickets:fila"))

    def test_sair_encerra_a_sessao(self):
        self.client.force_login(self.cliente)
        resposta = self.client.post(reverse("contas:sair"))
        self.assertRedirects(resposta, reverse("contas:entrada"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_sair_nao_aceita_get(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse("contas:sair")).status_code, 405)

    def test_logado_na_tela_de_entrada_vai_para_sua_pagina(self):
        self.client.force_login(self.cliente)
        self.assertRedirects(self.client.get(reverse("contas:entrada")), reverse("tickets:meus_tickets"))


class PermissaoPorPerfilTests(AcessoTestCase):
    """RNF04: cada perfil só acessa as próprias telas."""

    def test_sem_login_vai_para_a_entrada(self):
        for nome in ("tickets:meus_tickets", "tickets:fila"):
            url = reverse(nome)
            self.assertRedirects(self.client.get(url), f"{reverse('contas:entrada')}?next={url}")

    def test_raiz_sem_login_vai_para_a_entrada(self):
        self.assertRedirects(self.client.get("/"), reverse("contas:entrada"))

    def test_cliente_nao_acessa_a_fila(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse("tickets:fila")).status_code, 403)

    def test_equipe_nao_acessa_meus_tickets(self):
        self.client.force_login(self.atendente)
        self.assertEqual(self.client.get(reverse("tickets:meus_tickets")).status_code, 403)

    def test_cada_perfil_ve_o_proprio_menu(self):
        self.client.force_login(self.cliente)
        resposta = self.client.get(reverse("tickets:meus_tickets"))
        self.assertContains(resposta, "Meus tickets")
        self.assertNotContains(resposta, 'href="/fila/"')
        self.client.force_login(self.atendente)
        resposta = self.client.get(reverse("tickets:fila"))
        self.assertContains(resposta, 'href="/fila/"')
        self.assertNotContains(resposta, 'href="/meus-tickets/"')
