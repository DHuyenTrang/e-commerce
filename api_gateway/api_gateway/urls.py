from django.contrib import admin
from django.urls import path

from gateway.views import gateway_entrypoint

urlpatterns = [
    path("admin/", admin.site.urls),
    path("<path:path>", gateway_entrypoint),
]
