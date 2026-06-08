import uuid

from django.db import models


class Carrier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)


class ShippingRate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE, related_name="rates")
    province = models.CharField(max_length=120)
    base_fee = models.DecimalField(max_digits=12, decimal_places=2)
    fee_per_kg = models.DecimalField(max_digits=12, decimal_places=2)
    estimated_days = models.PositiveIntegerField(default=3)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["carrier", "province"], name="unique_carrier_province_rate"),
        ]


class Shipment(models.Model):
    class Status(models.TextChoices):
        CREATED = "CREATED"
        IN_TRANSIT = "IN_TRANSIT"
        DELIVERED = "DELIVERED"
        FAILED = "FAILED"
        CANCELLED = "CANCELLED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.UUIDField()
    carrier = models.ForeignKey(Carrier, on_delete=models.PROTECT, related_name="shipments")
    tracking_number = models.CharField(max_length=120, unique=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.CREATED)
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=2)
    receiver_address_snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def change_status(self, status):
        self.status = status
        self.save(update_fields=["status", "updated_at"])


class TrackingEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="events")
    status = models.CharField(max_length=24, choices=Shipment.Status.choices)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)
