from django.urls import path

from . import views

urlpatterns = [
    path("reviews", views.reviews),
    path("products/<uuid:product_id>/reviews", views.product_reviews),
    path("reviews/<uuid:review_id>/replies", views.replies),
    path("moderation/<str:target_type>/<uuid:target_id>", views.moderation),
]
