from django import forms

from .models import Categoria, Ticket


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
