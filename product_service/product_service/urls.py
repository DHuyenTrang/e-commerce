"""
URL configuration for product_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from catalog import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/products', views.list_products),
    path('api/v1/products/search', views.search_products),
    path('api/v1/products/admin/metadata/<str:metadata_type>', views.manage_metadata),
    path('api/v1/products/admin/products', views.admin_products),
    path('api/v1/products/admin/products/<uuid:product_id>', views.admin_product_detail),
    path('api/v1/products/admin/products/<uuid:product_id>/stock', views.admin_product_stock),
    path('api/v1/products/<str:product_id_or_slug>', views.product_detail),
]
