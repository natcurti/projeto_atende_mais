from django.urls import path

from . import views

app_name = "painel"

urlpatterns = [
    path("painel/", views.painel, name="painel"),
]
