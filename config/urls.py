"""Rotas principais do atende+: cada app tem as suas, incluídas aqui."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from contas.views import inicio

admin.site.site_header = "atende+ | área técnica"
admin.site.site_title = "atende+"
admin.site.index_title = "Dados do sistema"

urlpatterns = [
    path("", inicio, name="inicio"),
    path("", include("contas.urls")),
    path("", include("tickets.urls")),
    path("admin/", admin.site.urls),
]

# Em desenvolvimento, o próprio Django entrega os anexos enviados.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
