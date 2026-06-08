import uuid

from django.db import models


class Department(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE"
        INACTIVE = "INACTIVE"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class StaffAccount(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE"
        PENDING_ACTIVATION = "PENDING_ACTIVATION"
        LOCKED = "LOCKED"
        INACTIVE = "INACTIVE"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_code = models.CharField(max_length=32, unique=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="staff")
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_active(self):
        return self.status == self.Status.ACTIVE

    def lock(self):
        self.status = self.Status.LOCKED
        self.save(update_fields=["status", "updated_at"])

    def unlock(self):
        self.status = self.Status.ACTIVE
        self.save(update_fields=["status", "updated_at"])


class Permission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=120, unique=True)
    resource = models.CharField(max_length=64)
    action = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_system_role = models.BooleanField(default=False)
    permissions = models.ManyToManyField(Permission, through="RolePermission", related_name="roles")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_permissions(self, permission_ids):
        RolePermission.objects.filter(role=self).delete()
        RolePermission.objects.bulk_create(
            [RolePermission(role=self, permission_id=permission_id) for permission_id in permission_ids]
        )


class StaffRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(StaffAccount, on_delete=models.CASCADE, related_name="staff_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="staff_roles")
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.UUIDField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["staff", "role"], name="unique_staff_role"),
        ]


class RolePermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["role", "permission"], name="unique_role_permission"),
        ]
