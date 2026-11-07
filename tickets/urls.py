from django.urls import path

from . import views

app_name = "tickets"

urlpatterns = [
    # Cliente
    path("meus-tickets/", views.meus_tickets, name="meus_tickets"),
    path("meus-tickets/novo/", views.novo_ticket, name="novo_ticket"),
    path("meus-tickets/<int:numero>/", views.ticket_cliente, name="ticket_cliente"),
    path("meus-tickets/<int:numero>/avaliar/", views.avaliar_ticket, name="avaliar"),
    # Equipe
    path("fila/", views.fila, name="fila"),
    path("fila/<int:numero>/", views.ticket_equipe, name="ticket_equipe"),
    path("fila/<int:numero>/assumir/", views.assumir_ticket, name="assumir"),
    path("fila/<int:numero>/gerenciar/", views.gerenciar_ticket, name="gerenciar"),
    # Administração das categorias (RF05)
    path("administracao/categorias/nova/", views.nova_categoria, name="nova_categoria"),
    path("administracao/categorias/<int:pk>/", views.editar_categoria, name="editar_categoria"),
    path("administracao/categorias/<int:pk>/ativa/", views.alterar_categoria, name="alterar_categoria"),
]
