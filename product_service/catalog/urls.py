from django.urls import path

from . import views

urlpatterns = [
    path("", views.list_products),
    path("search", views.search_products),
    path("admin/metadata/<str:metadata_type>", views.manage_metadata),
    path("admin/products", views.admin_products),
    path("admin/products/<uuid:product_id>", views.admin_product_detail),
    path("admin/products/<uuid:product_id>/stock", views.admin_product_stock),
    path("<str:product_id_or_slug>", views.product_detail),
]
