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

    def test_usuario_desativado_nao_entra_e_ve_o_motivo(self):
        Usuario.objects.filter(pk=self.atendente.pk).update(is_active=False)  # RN12
        resposta = self.entrar("carlos@empresa.com")
        self.assertContains(resposta, "Este acesso foi desativado.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_desativado_com_senha_errada_nao_revela_nada(self):
        Usuario.objects.filter(pk=self.atendente.pk).update(is_active=False)
        resposta = self.entrar("carlos@empresa.com", "senha-errada")
        self.assertContains(resposta, "E-mail ou senha incorretos")
        self.assertNotContains(resposta, "desativado")

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


# ==========================================================
# F5: administração da equipe (RF04, RN12)
# ==========================================================

class AdministracaoEquipeTests(AcessoTestCase):
    def setUp(self):
        self.client.force_login(self.admin)

    def dados_pessoa(self, **mudancas):
        dados = {"nome": "Beatriz Nunes", "email": "Beatriz@Empresa.com", "perfil": "atendente",
                 "senha": "Suporte#Novo9", "senha_confirmacao": "Suporte#Novo9"}
        dados.update(mudancas)
        return dados

    def test_so_administrador_acessa(self):  # RNF04
        urls = [
            reverse("contas:administracao"), reverse("contas:nova_pessoa"),
            reverse("contas:editar_pessoa", args=[self.atendente.pk]),
        ]
        for usuario in (self.atendente, self.cliente):
            self.client.force_login(usuario)
            for url in urls:
                self.assertEqual(self.client.get(url).status_code, 403, (usuario, url))
            self.assertEqual(self.client.post(reverse("contas:alterar_acesso", args=[self.atendente.pk])).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(urls[0]).status_code, 302)

    def test_menu_administracao_so_para_administrador(self):
        self.assertContains(self.client.get(reverse("tickets:fila")), "Administração")
        self.client.force_login(self.atendente)
        self.assertNotContains(self.client.get(reverse("tickets:fila")), "Administração")

    def test_cadastra_atendente_que_ja_consegue_entrar(self):  # RF04
        resposta = self.client.post(reverse("contas:nova_pessoa"), self.dados_pessoa(), follow=True)
        self.assertRedirects(resposta, reverse("contas:administracao"))
        self.assertContains(resposta, "Beatriz Nunes agora faz parte da equipe")
        nova = Usuario.objects.get(email="beatriz@empresa.com")
        self.assertEqual((nova.perfil, nova.empresa), ("atendente", None))
        self.client.logout()
        self.assertRedirects(self.entrar("beatriz@empresa.com", "Suporte#Novo9"), reverse("tickets:fila"))

    def test_cadastro_valida_email_senha_e_perfil(self):
        r = self.client.post(reverse("contas:nova_pessoa"), self.dados_pessoa(email="CARLOS@empresa.com"))
        self.assertContains(r, "Já existe uma conta com este e-mail.")
        r = self.client.post(reverse("contas:nova_pessoa"), self.dados_pessoa(senha_confirmacao="Outra#Senha9"))
        self.assertContains(r, "As senhas não são iguais.")
        r = self.client.post(reverse("contas:nova_pessoa"), self.dados_pessoa(senha="", senha_confirmacao=""))
        self.assertTrue(r.context["form"].has_error("senha"))
        r = self.client.post(reverse("contas:nova_pessoa"), self.dados_pessoa(perfil="cliente"))
        self.assertTrue(r.context["form"].has_error("perfil"))
        self.assertFalse(Usuario.objects.filter(email="beatriz@empresa.com").exists())

    def test_edita_dados_e_senha_em_branco_mantem_a_atual(self):
        url = reverse("contas:editar_pessoa", args=[self.atendente.pk])
        self.client.post(url, {"nome": "Carlos A. Lima", "email": "carlos@empresa.com", "perfil": "administrador"})
        self.atendente.refresh_from_db()
        self.assertEqual((self.atendente.nome, self.atendente.perfil), ("Carlos A. Lima", "administrador"))
        self.assertTrue(self.atendente.check_password(SENHA))

    def test_edita_a_senha(self):
        url = reverse("contas:editar_pessoa", args=[self.atendente.pk])
        self.client.post(url, {"nome": "Carlos", "email": "carlos@empresa.com", "perfil": "atendente",
                               "senha": "Trocada#2026x", "senha_confirmacao": "Trocada#2026x"})
        self.atendente.refresh_from_db()
        self.assertTrue(self.atendente.check_password("Trocada#2026x"))

    def test_administrador_nao_muda_o_proprio_perfil(self):
        url = reverse("contas:editar_pessoa", args=[self.admin.pk])
        self.client.post(url, {"nome": "Juliana", "email": "juliana@empresa.com", "perfil": "atendente"})
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.perfil, "administrador")

    def test_cliente_nao_e_gerenciado_aqui(self):
        self.assertEqual(self.client.get(reverse("contas:editar_pessoa", args=[self.cliente.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("contas:alterar_acesso", args=[self.cliente.pk])).status_code, 404)

    def test_desativar_impede_o_login_e_reativar_devolve(self):  # RN12
        url = reverse("contas:alterar_acesso", args=[self.atendente.pk])
        resposta = self.client.post(url, follow=True)
        self.assertContains(resposta, "O acesso de Carlos foi desativado")
        self.atendente.refresh_from_db()
        self.assertFalse(self.atendente.is_active)
        self.client.logout()
        self.assertEqual(self.entrar("carlos@empresa.com").status_code, 200)  # não entra
        self.client.force_login(self.admin)
        self.client.post(url)
        self.atendente.refresh_from_db()
        self.assertTrue(self.atendente.is_active)

    def test_desativar_derruba_a_sessao_aberta(self):
        outro = self.client_class()
        outro.force_login(self.atendente)
        self.client.post(reverse("contas:alterar_acesso", args=[self.atendente.pk]))
        self.assertEqual(outro.get(reverse("tickets:fila")).status_code, 302)  # volta para o login

    def test_nao_desativa_a_si_mesmo(self):
        resposta = self.client.post(reverse("contas:alterar_acesso", args=[self.admin.pk]), follow=True)
        self.assertContains(resposta, "Você não pode desativar o seu próprio acesso.")
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_avisa_tickets_em_aberto_e_nome_continua_nos_tickets(self):  # RN12
        from tickets.models import Categoria, Ticket

        categoria = Categoria.objects.create(nome="Dúvida")
        ticket = Ticket.objects.create(
            cliente=self.cliente, categoria=categoria, titulo="T", descricao="D",
            situacao="em_atendimento", atendente=self.atendente,
        )
        resposta = self.client.post(reverse("contas:alterar_acesso", args=[self.atendente.pk]), follow=True)
        self.assertContains(resposta, "Carlos ainda tem 1 ticket em aberto")
        detalhe = self.client.get(reverse("tickets:ticket_equipe", args=[ticket.pk]))
        self.assertContains(detalhe, "Carlos")

    def test_alterar_acesso_so_por_post(self):
        self.assertEqual(self.client.get(reverse("contas:alterar_acesso", args=[self.atendente.pk])).status_code, 405)
