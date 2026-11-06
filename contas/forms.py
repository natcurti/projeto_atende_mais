from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm

from .managers import normalizar_email
from .models import Usuario


class EntrarForm(AuthenticationForm):
    """Login com e-mail e senha (RF02). O Django já recusa usuários desativados (RN12)."""

    username = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "voce@empresa.com", "autofocus": True}),
    )
    password = forms.CharField(
        label="Senha", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password"})
    )

    error_messages = {
        "invalid_login": "E-mail ou senha incorretos. Confira e tente de novo.",
        "inactive": "Este acesso foi desativado. Fale com o administrador do suporte.",
    }

    def clean_username(self):
        return normalizar_email(self.cleaned_data["username"])


class CadastroClienteForm(forms.ModelForm):
    """Cadastro de um novo cliente (RF01)."""

    senha = forms.CharField(
        label="Senha", strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="A senha precisa ter pelo menos 8 caracteres.",
    )
    senha_confirmacao = forms.CharField(
        label="Confirmar senha", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"})
    )

    class Meta:
        model = Usuario
        fields = ["nome", "email", "empresa"]
        widgets = {
            "nome": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "empresa": forms.TextInput(attrs={"autocomplete": "organization"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["empresa"].required = True
        self.fields["empresa"].help_text = ""

    def clean_email(self):
        email = normalizar_email(self.cleaned_data["email"])
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail. Use a opção Entrar.")
        return email

    def clean(self):
        dados = super().clean()
        senha, confirmacao = dados.get("senha"), dados.get("senha_confirmacao")
        if senha and confirmacao and senha != confirmacao:
            self.add_error("senha_confirmacao", "As senhas não são iguais.")
        if senha:
            # Valida tamanho mínimo, senhas comuns e senhas parecidas com o nome ou o e-mail.
            usuario = Usuario(nome=dados.get("nome", ""), email=dados.get("email", ""))
            try:
                password_validation.validate_password(senha, usuario)
            except forms.ValidationError as erro:
                self.add_error("senha", erro)
        return dados

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.perfil = Usuario.Perfil.CLIENTE
        usuario.set_password(self.cleaned_data["senha"])  # RNF03
        if commit:
            usuario.save()
        return usuario
