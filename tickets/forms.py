from django import forms

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
    Painel "Gerenciar ticket" (RF10, RF11).
    A situação só oferece as mudanças permitidas agora; o atendente só aparece para administradores.
    """

    situacao = forms.ChoiceField(label="Situação")
    atendente = forms.ModelChoiceField(label="Atendente", queryset=Usuario.objects.none(), empty_label=None)

    def __init__(self, *args, ticket, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticket = ticket
        atual = Ticket.Situacao(ticket.situacao)
        self.fields["situacao"].choices = [
            (atual.value, atual.label), *[(s.value, s.label) for s in situacoes_possiveis(ticket)]
        ]
        self.fields["situacao"].initial = atual.value

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
