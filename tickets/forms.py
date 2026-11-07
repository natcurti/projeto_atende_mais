from django import forms
from django.utils import timezone

from contas.models import Usuario

from .models import Categoria, Ticket
from .services import situacoes_possiveis


class NovoTicketForm(forms.ModelForm):
    """Abertura de ticket pelo cliente (RF06)."""

    class Meta:
        model = Ticket
        fields = ["titulo", "categoria", "descricao"]
        widgets = {
            "titulo": forms.TextInput(attrs={"maxlength": 120}),
            "descricao": forms.Textarea(attrs={"rows": 7}),
        }
        help_texts = {
            "titulo": "Resuma o problema em uma frase. Ex.: Erro ao emitir nota fiscal",
            "descricao": "O que você fez, o que esperava que acontecesse e o que aconteceu.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # RN12: categorias desativadas não aparecem para novos tickets.
        self.fields["categoria"].queryset = Categoria.objects.filter(ativa=True)
        self.fields["categoria"].empty_label = "Escolha uma categoria"


class RespostaForm(forms.Form):
    """Nova mensagem na conversa do ticket (RF12)."""

    texto = forms.CharField(
        label="Responder",
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Escreva sua mensagem"}),
        error_messages={"required": "Escreva a mensagem antes de enviar."},
    )


class MensagemEquipeForm(RespostaForm):
    """
    Mensagem da equipe: ao cliente (RF12) ou nota interna (RF13).
    Quem não pode atuar no ticket (RN05) só pode escrever nota interna.
    """

    CLIENTE, INTERNA = "cliente", "interna"

    tipo = forms.ChoiceField(
        label="Tipo de mensagem", required=False,
        choices=[(CLIENTE, "Mensagem ao cliente"), (INTERNA, "Nota interna")],
        initial=CLIENTE, widget=forms.RadioSelect,
    )

    def __init__(self, *args, pode_responder_cliente=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["texto"].label = "Mensagem"
        self.fields["texto"].widget.attrs["placeholder"] = "Escreva a resposta ou a nota"
        if not pode_responder_cliente:
            self.fields["tipo"].choices = [(self.INTERNA, "Nota interna")]
            self.fields["tipo"].initial = self.INTERNA

    def clean_tipo(self):
        # Sem escolha, vale a primeira opção disponível (mensagem ao cliente, ou nota para quem só pode anotar).
        return self.cleaned_data["tipo"] or self.fields["tipo"].choices[0][0]

    @property
    def interna(self):
        return self.cleaned_data.get("tipo") == self.INTERNA


class FiltroFilaForm(forms.Form):
    """Filtros da fila de atendimento (RF08). Todos são opcionais e podem ser combinados."""

    situacao = forms.ChoiceField(
        label="Situação", required=False,
        choices=[("", "Todas em aberto"), *Ticket.Situacao.choices],
    )
    categoria = forms.ModelChoiceField(
        label="Categoria", required=False, queryset=Categoria.objects.all(), empty_label="Todas",
    )
    prioridade = forms.ChoiceField(
        label="Prioridade", required=False, choices=[("", "Todas"), *Ticket.Prioridade.choices],
    )
    atendente = forms.ChoiceField(label="Atendente", required=False)
    atrasados = forms.BooleanField(label="Só atrasados", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        equipe = Usuario.objects.filter(
            perfil__in=[Usuario.Perfil.ATENDENTE, Usuario.Perfil.ADMINISTRADOR], is_active=True
        ).order_by("nome")
        self.fields["atendente"].choices = [
            ("", "Todos"), ("comigo", "Comigo"), ("sem", "Sem atendente"),
            *[(str(u.pk), u.nome) for u in equipe],
        ]

    @property
    def filtros(self):
        """
        Filtros prontos para services.fila_de_atendimento.
        Um valor inválido na URL (ex.: ?prioridade=xyz) é ignorado, e os outros filtros continuam valendo.
        """
        self.is_valid()
        dados = self.cleaned_data
        return {
            "situacao": dados.get("situacao", ""),
            "categoria": dados.get("categoria"),
            "prioridade": dados.get("prioridade", ""),
            "atendente": dados.get("atendente", ""),
            "so_atrasados": dados.get("atrasados", False),
        }

    @property
    def tem_filtro(self):
        return any(self.filtros.values())


class GerenciarTicketForm(forms.Form):
    """
    Painel "Gerenciar ticket" (RF10, RF11, RF17).
    A situação só oferece as mudanças permitidas agora; o atendente só aparece para administradores;
    a prioridade mostra o prazo de cada opção (RN09).
    """

    situacao = forms.ChoiceField(label="Situação")
    prioridade = forms.ChoiceField(
        label="Prioridade", required=False,
        choices=[
            ("urgente", "Urgente (4 horas)"), ("alta", "Alta (1 dia)"),
            ("media", "Média (3 dias)"), ("baixa", "Baixa (5 dias)"),
        ],
    )
    atendente = forms.ModelChoiceField(label="Atendente", queryset=Usuario.objects.none(), empty_label=None)

    def __init__(self, *args, ticket, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticket = ticket
        atual = Ticket.Situacao(ticket.situacao)
        self.fields["situacao"].choices = [
            (atual.value, atual.label), *[(s.value, s.label) for s in situacoes_possiveis(ticket)]
        ]
        self.fields["situacao"].initial = atual.value
        self.fields["prioridade"].initial = ticket.prioridade
        self.fields["prioridade"].help_text = (
            f"Prazo atual: {timezone.localtime(ticket.prazo):%d/%m, %H:%M}. "
            "Muda junto com a prioridade, contado a partir da abertura."
        )

        if usuario.perfil == Usuario.Perfil.ADMINISTRADOR:
            self.fields["atendente"].queryset = Usuario.objects.filter(
                perfil__in=[Usuario.Perfil.ATENDENTE, Usuario.Perfil.ADMINISTRADOR], is_active=True
            ).order_by("nome")
            self.fields["atendente"].initial = ticket.atendente_id
            if ticket.atendente_id is None:
                self.fields["atendente"].required = False
                self.fields["atendente"].empty_label = "Ninguém ainda"
        else:
            del self.fields["atendente"]

    def clean_prioridade(self):
        # Sem prioridade enviada, vale a atual (nada muda).
        return self.cleaned_data["prioridade"] or self.ticket.prioridade


class CategoriaForm(forms.ModelForm):
    """Cadastro e renomeação de categorias (RF05)."""

    class Meta:
        model = Categoria
        fields = ["nome"]
        labels = {"nome": "Nome da categoria"}
        widgets = {"nome": forms.TextInput(attrs={"placeholder": "Ex.: Integrações", "maxlength": 60})}

    def clean_nome(self):
        nome = " ".join(self.cleaned_data["nome"].split())  # tira espaços repetidos
        # A comparação é feita no Python porque o SQLite só ignora maiúsculas em letras sem acento
        # ("DÚVIDA" e "Dúvida" seriam diferentes para ele). As categorias são poucas.
        outras = Categoria.objects.exclude(pk=self.instance.pk).values_list("nome", flat=True)
        if any(existente.casefold() == nome.casefold() for existente in outras):
            raise forms.ValidationError("Já existe uma categoria com este nome.")
        return nome


class AvaliacaoForm(forms.Form):
    """Avaliação do atendimento pela cliente (RF16): nota de 1 a 5 e comentário opcional."""

    nota = forms.TypedChoiceField(
        label="Nota", coerce=int, choices=[(n, f"{n} de 5") for n in range(1, 6)], widget=forms.RadioSelect,
        error_messages={"required": "Escolha de 1 a 5 estrelas."},
    )
    comentario = forms.CharField(
        label="Comentário (opcional)", required=False, max_length=500,
        widget=forms.Textarea(attrs={"rows": 3, "maxlength": 500}),
    )
