from django.urls import path

from . import views

urlpatterns = [
    path("methods", views.methods),
    path("admin/methods", views.admin_methods),
    path("transactions", views.transactions),
    path("transactions/<uuid:transaction_id>/status", views.transaction_status),
    path("callbacks/<str:provider>", views.callbacks),
]
