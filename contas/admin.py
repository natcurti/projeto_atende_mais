from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from .models import Usuario


class UsuarioCriacaoForm(AdminUserCreationForm):
    class Meta:
        model = Usuario
        fields = ("email", "nome", "perfil", "empresa")


class UsuarioEdicaoForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = "__all__"


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Área de administração técnica (/admin). As telas do sistema para o administrador vêm no MVP."""

    add_form = UsuarioCriacaoForm
    form = UsuarioEdicaoForm

    list_display = ("nome", "email", "perfil", "empresa", "is_active")
    list_filter = ("perfil", "is_active")
    search_fields = ("nome", "email", "empresa")
    ordering = ("nome",)
    readonly_fields = ("last_login", "criado_em")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Dados pessoais", {"fields": ("nome", "perfil", "empresa")}),
        ("Acesso", {"fields": ("is_active", "is_superuser")}),
        ("Datas", {"fields": ("criado_em", "last_login")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "nome", "perfil", "empresa", "usable_password", "password1", "password2")}),
    )
    filter_horizontal = ()
