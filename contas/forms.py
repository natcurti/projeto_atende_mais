from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm

from .managers import normalizar_email
from .models import Usuario


class EntrarForm(AuthenticationForm):
    """Login com e-mail e senha (RF02). Usuários desativados não entram (RN12)."""

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

    def clean(self):
        try:
            return super().clean()
        except forms.ValidationError as erro:
            # O Django recusa usuários desativados como se a senha estivesse errada.
            # Com a senha certa, dizemos o motivo real; com a senha errada, nada é revelado.
            if self._desativado_com_senha_certa():
                raise forms.ValidationError(self.error_messages["inactive"], code="inactive") from None
            raise erro

    def _desativado_com_senha_certa(self):
        email, senha = self.cleaned_data.get("username"), self.cleaned_data.get("password")
        if not email or not senha:
            return False
        usuario = Usuario.objects.filter(email=email, is_active=False).first()
        return usuario is not None and usuario.check_password(senha)


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


class PessoaEquipeForm(forms.ModelForm):
    """
    Cadastro e edição de atendentes e administradores (RF04).
    Na criação, a senha inicial é obrigatória; na edição, em branco mantém a senha atual.
    """

    perfil = forms.ChoiceField(
        label="Perfil",
        choices=[(Usuario.Perfil.ATENDENTE, "Atendente"), (Usuario.Perfil.ADMINISTRADOR, "Administrador")],
    )
    senha = forms.CharField(
        label="Senha inicial", strip=False, required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    senha_confirmacao = forms.CharField(
        label="Confirmar senha", strip=False, required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = Usuario
        fields = ["nome", "email", "perfil"]

    def __init__(self, *args, editor, **kwargs):
        super().__init__(*args, **kwargs)
        self.editor = editor
        self.criando = self.instance.pk is None
        if self.criando:
            self.fields["senha"].required = True
            self.fields["senha_confirmacao"].required = True
            self.fields["senha"].help_text = "Pelo menos 8 caracteres. Passe para a pessoa trocar depois."
        else:
            self.fields["senha"].label = "Nova senha"
            self.fields["senha"].help_text = "Deixe em branco para manter a senha atual."
        if self.instance.pk == editor.pk:
            # Ninguém tira o próprio perfil de administrador (o sistema ficaria sem quem administre).
            self.fields["perfil"].disabled = True
            self.fields["perfil"].help_text = "Você não pode mudar o seu próprio perfil."

    def clean_email(self):
        email = normalizar_email(self.cleaned_data["email"])
        if Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email

    def clean(self):
        dados = super().clean()
        senha, confirmacao = dados.get("senha"), dados.get("senha_confirmacao")
        if senha or confirmacao:
            if senha != confirmacao:
                self.add_error("senha_confirmacao", "As senhas não são iguais.")
            elif senha:
                usuario = Usuario(nome=dados.get("nome", ""), email=dados.get("email", ""))
                try:
                    password_validation.validate_password(senha, usuario)
                except forms.ValidationError as erro:
                    self.add_error("senha", erro)
        return dados

    def save(self, commit=True):
        pessoa = super().save(commit=False)
        pessoa.empresa = None
        if self.cleaned_data.get("senha"):
            pessoa.set_password(self.cleaned_data["senha"])  # RNF03
        if commit:
            pessoa.save()
        return pessoa
