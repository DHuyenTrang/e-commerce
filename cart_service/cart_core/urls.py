from django.urls import path

from . import views

urlpatterns = [
    path("", views.cart_detail),
    path("items", views.cart_items),
    path("items/<uuid:item_id>", views.cart_item_detail),
]
