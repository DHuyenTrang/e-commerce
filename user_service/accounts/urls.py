from django.urls import path

from . import views

urlpatterns = [
    path("auth/register", views.register),
    path("auth/login", views.login),
    path("auth/logout", views.logout),
    path("me", views.profile),
    path("me/addresses", views.addresses),
    path("me/addresses/<uuid:address_id>", views.address_detail),
]
