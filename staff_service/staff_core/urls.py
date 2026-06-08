from django.urls import path

from . import views

urlpatterns = [
    path("departments", views.departments),
    path("permissions", views.permissions),
    path("roles", views.roles),
    path("roles/<uuid:role_id>/permissions", views.role_permissions),
    path("members", views.staff_members),
    path("members/<uuid:staff_id>/department", views.staff_department),
    path("members/<uuid:staff_id>/status", views.staff_status),
    path("members/<uuid:staff_id>/roles", views.staff_roles),
]
