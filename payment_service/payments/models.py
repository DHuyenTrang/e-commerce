import uuid

from django.db import models
from django.utils import timezone


class PaymentMethod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=120)
    provider = models.CharField(max_length=32)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)


class PaymentTransaction(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        SUCCESS = "SUCCESS"
        FAILED = "FAILED"
        CANCELLED = "CANCELLED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.UUIDField()
    transaction_code = models.CharField(max_length=120, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="VND")
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, related_name="transactions")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    gateway_reference = models.CharField(max_length=120, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_success(self, reference):
        if self.status == self.Status.SUCCESS:
            return
        self.status = self.Status.SUCCESS
        self.gateway_reference = reference
        self.paid_at = timezone.now()
        self.save(update_fields=["status", "gateway_reference", "paid_at", "updated_at"])

    def mark_failed(self, reason):
        if self.status == self.Status.SUCCESS:
            return
        self.status = self.Status.FAILED
        self.failure_reason = reason
        self.save(update_fields=["status", "failure_reason", "updated_at"])


class PaymentGatewayCallback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.CASCADE, related_name="callbacks")
    provider = models.CharField(max_length=32)
    payload = models.JSONField(default=dict)
    signature_valid = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)
