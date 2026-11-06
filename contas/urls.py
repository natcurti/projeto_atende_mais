from django.urls import path

from . import views

app_name = "contas"

urlpatterns = [
    path("entrar/", views.entrada, name="entrada"),
    path("sair/", views.sair, name="sair"),
]
