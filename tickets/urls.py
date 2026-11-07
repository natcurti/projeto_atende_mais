from django.urls import path

from . import views

app_name = "tickets"

urlpatterns = [
    # Cliente
    path("meus-tickets/", views.meus_tickets, name="meus_tickets"),
    path("meus-tickets/novo/", views.novo_ticket, name="novo_ticket"),
    path("meus-tickets/<int:numero>/", views.ticket_cliente, name="ticket_cliente"),
    # Equipe
    path("fila/", views.fila, name="fila"),
]
