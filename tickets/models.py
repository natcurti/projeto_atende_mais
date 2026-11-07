"""
Models do atendimento: as tabelas da Entrega 4, com as mesmas restrições.
As restrições ficam em Meta.constraints e o `migrate` as cria no banco.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Length, Trim
from django.db.models.lookups import GreaterThan
from django.utils import timezone

TAMANHO_MAXIMO_ANEXO = 5 * 1024 * 1024  # 5 MB (RN14)


class Categoria(models.Model):
    """Assunto em que o ticket é classificado (RF05)."""

    nome = models.CharField(max_length=60, unique=True)
    ativa = models.BooleanField(default=True, help_text="Categorias inativas não aparecem em novos tickets (RN12).")
    criada_em = models.DateTimeField("criada em", default=timezone.now)

    class Meta:
        db_table = "categoria"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Ticket(models.Model):
    """Pedido de suporte de um cliente (RF06). O id é o número exibido, a partir de 1000 (RN01)."""

    class Situacao(models.TextChoices):
        ABERTO = "aberto", "Aberto"
        EM_ATENDIMENTO = "em_atendimento", "Em atendimento"
        AGUARDANDO_CLIENTE = "aguardando_cliente", "Aguardando cliente"
        RESOLVIDO = "resolvido", "Resolvido"
        FECHADO = "fechado", "Fechado"

    class Prioridade(models.TextChoices):
        URGENTE = "urgente", "Urgente"
        ALTA = "alta", "Alta"
        MEDIA = "media", "Média"
        BAIXA = "baixa", "Baixa"

    titulo = models.CharField("título", max_length=120)
    descricao = models.TextField("descrição")
    situacao = models.CharField("situação", max_length=18, choices=Situacao.choices, default=Situacao.ABERTO)
    prioridade = models.CharField(max_length=7, choices=Prioridade.choices, default=Prioridade.MEDIA)
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tickets_abertos"
    )
    atendente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tickets_atendidos",
        null=True, blank=True,
    )
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="tickets")
    aberto_em = models.DateTimeField("aberto em", default=timezone.now)
    prazo = models.DateTimeField(blank=True, help_text="Calculado pela prioridade se ficar vazio (RN09).")
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)
    resolvido_em = models.DateTimeField("resolvido em", null=True, blank=True)
    fechado_em = models.DateTimeField("fechado em", null=True, blank=True)

    class Meta:
        db_table = "ticket"
        ordering = ["-atualizado_em"]
        indexes = [models.Index(fields=["situacao", "prazo"], name="ix_ticket_situacao_prazo")]
        constraints = [
            models.CheckConstraint(
                condition=Q(situacao__in=["aberto", "em_atendimento", "aguardando_cliente", "resolvido", "fechado"]),
                name="ck_ticket_situacao",
                violation_error_message="Situação inválida.",
            ),
            models.CheckConstraint(
                condition=Q(prioridade__in=["urgente", "alta", "media", "baixa"]),
                name="ck_ticket_prioridade",
                violation_error_message="Prioridade inválida.",
            ),
            # RN03 e RN04: Aberto <=> sem atendente
            models.CheckConstraint(
                condition=(Q(situacao="aberto") & Q(atendente__isnull=True))
                | (~Q(situacao="aberto") & Q(atendente__isnull=False)),
                name="ck_ticket_atendente",
                violation_error_message="Um ticket Aberto não tem atendente; nas demais situações, o atendente é obrigatório.",
            ),
            models.CheckConstraint(
                condition=Q(prazo__gt=F("aberto_em")),
                name="ck_ticket_prazo",
                violation_error_message="O prazo precisa ser depois da abertura do ticket.",
            ),
            models.CheckConstraint(
                condition=~Q(situacao__in=["resolvido", "fechado"]) | Q(resolvido_em__isnull=False),
                name="ck_ticket_resolvido",
                violation_error_message="Informe a data de resolução para tickets resolvidos ou fechados.",
            ),
            models.CheckConstraint(
                condition=~Q(situacao="fechado") | Q(fechado_em__isnull=False),
                name="ck_ticket_fechado",
                violation_error_message="Informe a data de fechamento para tickets fechados.",
            ),
        ]

    def __str__(self):
        return f"{self.numero} {self.titulo}"

    @property
    def numero(self):
        return f"#{self.pk}" if self.pk else "(novo)"

    @property
    def atrasado(self):
        """RN10: prazo vencido e ainda não resolvido."""
        nao_resolvido = self.situacao in (
            self.Situacao.ABERTO, self.Situacao.EM_ATENDIMENTO, self.Situacao.AGUARDANDO_CLIENTE,
        )
        return nao_resolvido and self.prazo is not None and self.prazo < timezone.now()

    @property
    def aceita_resposta(self):
        """Resolvidos e fechados não recebem mensagens (a reabertura, RF15, vem depois do MVP)."""
        return self.situacao not in (self.Situacao.RESOLVIDO, self.Situacao.FECHADO)

    def save(self, *args, **kwargs):
        if self.prazo is None:
            # Importado aqui porque services.py também importa este arquivo.
            from .services import calcular_prazo

            self.prazo = calcular_prazo(self.prioridade, self.aberto_em)
        super().save(*args, **kwargs)


class Mensagem(models.Model):
    """Mensagem da conversa do ticket, ao cliente ou interna da equipe (RF12, RF13)."""

    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name="mensagens")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="mensagens")
    texto = models.TextField()
    interna = models.BooleanField(default=False, help_text="Nota interna: nunca aparece para o cliente (RN08).")
    criada_em = models.DateTimeField("criada em", default=timezone.now)

    class Meta:
        db_table = "mensagem"
        verbose_name_plural = "mensagens"
        ordering = ["criada_em"]
        indexes = [models.Index(fields=["ticket", "criada_em"], name="ix_mensagem_ticket")]
        constraints = [
            models.CheckConstraint(
                condition=GreaterThan(Length(Trim("texto")), 0),
                name="ck_mensagem_texto",
                violation_error_message="A mensagem não pode ficar vazia.",
            ),
        ]

    def __str__(self):
        return f"Mensagem de {self.autor} em {self.ticket.numero}"


class Anexo(models.Model):
    """Arquivo enviado no ticket, na abertura ou junto de uma mensagem (RF14, RN14)."""

    class Tipo(models.TextChoices):
        JPG = "jpg", "JPG"
        PNG = "png", "PNG"
        PDF = "pdf", "PDF"

    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name="anexos")
    mensagem = models.ForeignKey(
        Mensagem, on_delete=models.PROTECT, related_name="anexos", null=True, blank=True
    )
    enviado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="anexos")
    arquivo = models.FileField(upload_to="anexos/%Y/%m/", max_length=255)
    nome_original = models.CharField(max_length=255)
    tipo = models.CharField(max_length=4, choices=Tipo.choices)
    tamanho_bytes = models.PositiveIntegerField("tamanho (bytes)")
    enviado_em = models.DateTimeField("enviado em", default=timezone.now)

    class Meta:
        db_table = "anexo"
        constraints = [
            models.CheckConstraint(
                condition=Q(tipo__in=["jpg", "png", "pdf"]),
                name="ck_anexo_tipo",
                violation_error_message="O anexo precisa ser JPG, PNG ou PDF.",
            ),
            models.CheckConstraint(
                condition=Q(tamanho_bytes__gte=1, tamanho_bytes__lte=TAMANHO_MAXIMO_ANEXO),
                name="ck_anexo_tamanho",
                violation_error_message="O anexo pode ter no máximo 5 MB.",
            ),
        ]

    def __str__(self):
        return self.nome_original


class Historico(models.Model):
    """Registro automático de uma mudança no ticket (RN13)."""

    class Campo(models.TextChoices):
        SITUACAO = "situacao", "Situação"
        ATENDENTE = "atendente", "Atendente"
        PRIORIDADE = "prioridade", "Prioridade"

    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name="historico")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="alteracoes")
    campo = models.CharField(max_length=10, choices=Campo.choices)
    valor_anterior = models.CharField("valor anterior", max_length=150, null=True, blank=True)
    valor_novo = models.CharField("valor novo", max_length=150, null=True, blank=True)
    alterado_em = models.DateTimeField("alterado em", default=timezone.now)

    class Meta:
        db_table = "historico"
        verbose_name = "histórico"
        verbose_name_plural = "histórico"
        ordering = ["alterado_em"]
        indexes = [models.Index(fields=["ticket", "alterado_em"], name="ix_historico_ticket")]
        constraints = [
            models.CheckConstraint(
                condition=Q(campo__in=["situacao", "atendente", "prioridade"]), name="ck_historico_campo",
                violation_error_message="Campo de histórico inválido.",
            ),
            # Só grava se algo mudou (comparação que considera valores vazios).
            models.CheckConstraint(
                condition=(Q(valor_anterior__isnull=True) & Q(valor_novo__isnull=False))
                | (Q(valor_anterior__isnull=False) & Q(valor_novo__isnull=True))
                | (Q(valor_anterior__isnull=False) & Q(valor_novo__isnull=False) & ~Q(valor_anterior=F("valor_novo"))),
                name="ck_historico_mudou",
                violation_error_message="O valor novo precisa ser diferente do anterior.",
            ),
        ]

    def __str__(self):
        return f"{self.ticket.numero}: {self.descricao}"

    @property
    def descricao(self):
        """Frase do evento como aparece na conversa do ticket."""
        if self.campo == self.Campo.ATENDENTE:
            if self.valor_anterior is None and self.autor.nome == self.valor_novo:
                return f"{self.valor_novo} assumiu o atendimento"
            return f"{self.autor.nome} passou o atendimento para {self.valor_novo}"
        if self.campo == self.Campo.SITUACAO:
            novo = Ticket.Situacao(self.valor_novo).label
            if self.valor_novo == Ticket.Situacao.RESOLVIDO:
                return f"{self.autor.nome} marcou o ticket como resolvido"
            if self.valor_anterior is None:
                return f"Situação: {novo}"
            return f"Situação alterada de {Ticket.Situacao(self.valor_anterior).label} para {novo}"
        anterior = Ticket.Prioridade(self.valor_anterior).label if self.valor_anterior else "sem prioridade"
        return f"Prioridade alterada de {anterior} para {Ticket.Prioridade(self.valor_novo).label}"


class Avaliacao(models.Model):
    """Nota do cliente depois da resolução: uma por ticket (RF16, RN11)."""

    ticket = models.OneToOneField(Ticket, on_delete=models.PROTECT, related_name="avaliacao")
    nota = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.CharField("comentário", max_length=500, null=True, blank=True)
    avaliado_em = models.DateTimeField("avaliado em", default=timezone.now)

    class Meta:
        db_table = "avaliacao"
        verbose_name = "avaliação"
        verbose_name_plural = "avaliações"
        constraints = [
            models.CheckConstraint(
                condition=Q(nota__gte=1, nota__lte=5),
                name="ck_avaliacao_nota",
                violation_error_message="A nota precisa ser de 1 a 5.",
            ),
        ]

    def __str__(self):
        return f"{self.ticket.numero}: nota {self.nota}"
