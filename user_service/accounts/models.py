import uuid

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone


class UserAccount(models.Model):
    class Status(models.TextChoices):
        PENDING_VERIFICATION = "PENDING_VERIFICATION"
        ACTIVE = "ACTIVE"
        LOCKED = "LOCKED"
        INACTIVE = "INACTIVE"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, unique=True)
    password_hash = models.CharField(max_length=255)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    def is_login_allowed(self):
        return self.status == self.Status.ACTIVE


class CustomerProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = "MALE"
        FEMALE = "FEMALE"
        OTHER = "OTHER"
        UNSPECIFIED = "UNSPECIFIED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=255)
    avatar_url = models.URLField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=16, choices=Gender.choices, default=Gender.UNSPECIFIED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name="addresses")
    recipient_name = models.CharField(max_length=255)
    recipient_phone = models.CharField(max_length=32)
    province = models.CharField(max_length=120)
    district = models.CharField(max_length=120)
    ward = models.CharField(max_length=120)
    detail = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def soft_delete(self):
        self.is_deleted = True
        self.save(update_fields=["is_deleted", "updated_at"])


class UserSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name="sessions")
    refresh_token_hash = models.CharField(max_length=255)
    device_info = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def revoke(self):
        self.revoked_at = timezone.now()
        self.save(update_fields=["revoked_at"])

    def is_active(self):
        return self.revoked_at is None and self.expires_at > timezone.now()
