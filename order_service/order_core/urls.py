from django.urls import path

from . import views


urlpatterns = [
    path("checkout/initiate", views.initiate_checkout),
    path("checkout/place-order", views.place_order),
    path("me", views.list_user_orders),
    path("me/<uuid:order_id>", views.get_order_detail),
    path("me/<uuid:order_id>/cancel-request", views.cancel_order_request),
    path("admin/orders", views.list_all_orders),
    path("admin/orders/<uuid:order_id>/status", views.update_order_status),
]
