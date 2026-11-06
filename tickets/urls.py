from django.urls import path

from . import views

app_name = "tickets"

urlpatterns = [
    path("meus-tickets/", views.meus_tickets, name="meus_tickets"),
    path("fila/", views.fila, name="fila"),
]
