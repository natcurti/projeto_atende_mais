"""Área de administração técnica (/admin): serve para conferir os dados durante o desenvolvimento."""

from django.contrib import admin

from .models import Anexo, Avaliacao, Categoria, Historico, Mensagem, Ticket


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativa", "criada_em")
    list_filter = ("ativa",)
    search_fields = ("nome",)


class MensagemInline(admin.TabularInline):
    model = Mensagem
    extra = 0
    fields = ("autor", "texto", "interna", "criada_em")


class HistoricoInline(admin.TabularInline):
    model = Historico
    extra = 0
    fields = ("campo", "valor_anterior", "valor_novo", "autor", "alterado_em")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("numero", "titulo", "cliente", "categoria", "prioridade", "situacao", "atendente", "prazo", "atrasado")
    list_filter = ("situacao", "prioridade", "categoria")
    search_fields = ("id", "titulo", "cliente__nome", "cliente__empresa")
    readonly_fields = ("atualizado_em",)
    inlines = [MensagemInline, HistoricoInline]

    @admin.display(boolean=True, description="atrasado")
    def atrasado(self, ticket):
        return ticket.atrasado

    @admin.display(description="nº", ordering="id")
    def numero(self, ticket):
        return ticket.numero


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = ("ticket", "autor", "interna", "criada_em")
    list_filter = ("interna",)


@admin.register(Anexo)
class AnexoAdmin(admin.ModelAdmin):
    list_display = ("nome_original", "ticket", "tipo", "tamanho_bytes", "enviado_por", "enviado_em")


@admin.register(Historico)
class HistoricoAdmin(admin.ModelAdmin):
    list_display = ("ticket", "campo", "valor_anterior", "valor_novo", "autor", "alterado_em")
    list_filter = ("campo",)


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ("ticket", "nota", "avaliado_em")
    list_filter = ("nota",)
