from django.db import IntegrityError
from django.test import TestCase

from .models import Usuario


class CriacaoDeUsuarioTests(TestCase):
    def test_cliente_entra_pelo_email_e_senha_vira_hash(self):
        usuario = Usuario.objects.create_user(
            "Maria@Exemplo.com", "senha-forte-123", nome="Maria", empresa="Souza ME"
        )
        self.assertEqual(usuario.email, "Maria@exemplo.com")  # domínio do e-mail normalizado
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
