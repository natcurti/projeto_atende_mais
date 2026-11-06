from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .managers import UsuarioManager


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Pessoa que usa o sistema: cliente, atendente ou administrador (tabela `usuario` da Entrega 4)."""

    class Perfil(models.TextChoices):
        CLIENTE = "cliente", "Cliente"
        ATENDENTE = "atendente", "Atendente"
        ADMINISTRADOR = "administrador", "Administrador"

    nome = models.CharField("nome completo", max_length=150)
    email = models.EmailField("e-mail", max_length=254, unique=True)
    perfil = models.CharField(max_length=13, choices=Perfil.choices, default=Perfil.CLIENTE)
    empresa = models.CharField(max_length=150, blank=True, null=True, help_text="Obrigatória para clientes.")
    criado_em = models.DateTimeField("criado em", default=timezone.now)

    # Campos exigidos pelo login do Django, com os nomes de coluna da Entrega 4.
    password = models.CharField("senha", max_length=128, db_column="senha_hash")
    last_login = models.DateTimeField("último acesso", blank=True, null=True, db_column="ultimo_acesso")
    is_active = models.BooleanField(
        "ativo", default=True, db_column="ativo", help_text="Desmarque para impedir o login (RN12)."
    )

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["nome"]

    class Meta:
        db_table = "usuario"
        verbose_name = "usuário"
        verbose_name_plural = "usuários"
        ordering = ["nome"]
        constraints = [
            models.CheckConstraint(
                condition=Q(perfil__in=["cliente", "atendente", "administrador"]),
                name="ck_usuario_perfil",
                violation_error_message="Perfil inválido.",
            ),
            models.CheckConstraint(
                condition=~Q(perfil="cliente") | (Q(empresa__isnull=False) & ~Q(empresa="")),
                name="ck_usuario_empresa",
                violation_error_message="Clientes precisam informar a empresa.",
            ),
        ]

    def __str__(self):
        return self.nome

    @property
    def is_staff(self):
        """Quem pode abrir a área de administração técnica do Django (/admin)."""
        return self.is_superuser or self.perfil == self.Perfil.ADMINISTRADOR

    @property
    def eh_cliente(self):
        return self.perfil == self.Perfil.CLIENTE

    @property
    def eh_equipe(self):
        """Atendentes e administradores: quem trabalha na fila."""
        return self.perfil in (self.Perfil.ATENDENTE, self.Perfil.ADMINISTRADOR)
