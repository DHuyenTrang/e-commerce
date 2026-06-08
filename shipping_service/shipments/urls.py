from django.urls import path

from . import views

urlpatterns = [
    path("track/<str:tracking_number>", views.track),
    path("fees", views.fees),
    path("admin/carriers", views.carriers),
    path("admin/rates", views.rates),
    path("admin/shipments", views.shipments),
    path("admin/shipments/<uuid:shipment_id>/tracking", views.shipment_tracking),
]
