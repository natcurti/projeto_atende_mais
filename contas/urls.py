from django.urls import path

from . import views

app_name = "contas"

urlpatterns = [
    path("entrar/", views.entrada, name="entrada"),
    path("sair/", views.sair, name="sair"),
    # Administração (RF04)
    path("administracao/", views.administracao, name="administracao"),
    path("administracao/equipe/nova/", views.nova_pessoa, name="nova_pessoa"),
    path("administracao/equipe/<int:pk>/", views.editar_pessoa, name="editar_pessoa"),
    path("administracao/equipe/<int:pk>/acesso/", views.alterar_acesso, name="alterar_acesso"),
]
