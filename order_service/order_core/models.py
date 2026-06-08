import uuid

from django.db import models
from django.utils import timezone


class CheckoutSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE"
        PLACED = "PLACED"
        EXPIRED = "EXPIRED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField()
    cart_id = models.UUIDField()
    shipping_address_id = models.CharField(max_length=120, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_address_snapshot = models.JSONField(default=dict, blank=True)
    items_snapshot = models.JSONField(default=list)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_usable(self):
        return self.status == self.Status.ACTIVE and self.expires_at > timezone.now()

    def mark_placed(self):
        self.status = self.Status.PLACED
        self.save(update_fields=["status", "updated_at"])


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "PENDING_PAYMENT"
        CONFIRMED = "CONFIRMED"
        PROCESSING = "PROCESSING"
        SHIPPING = "SHIPPING"
        COMPLETED = "COMPLETED"
        CANCEL_REQUESTED = "CANCEL_REQUESTED"
        CANCELLED = "CANCELLED"
        REFUNDED = "REFUNDED"

    VALID_TRANSITIONS = {
        Status.PENDING_PAYMENT: {Status.CONFIRMED, Status.CANCELLED},
        Status.CONFIRMED: {Status.PROCESSING, Status.CANCEL_REQUESTED, Status.CANCELLED},
        Status.PROCESSING: {Status.SHIPPING, Status.CANCEL_REQUESTED, Status.CANCELLED},
        Status.SHIPPING: {Status.COMPLETED},
        Status.COMPLETED: {Status.REFUNDED},
        Status.CANCEL_REQUESTED: {Status.CANCELLED, Status.CONFIRMED, Status.PROCESSING},
        Status.CANCELLED: set(),
        Status.REFUNDED: set(),
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_code = models.CharField(max_length=32, unique=True)
    user_id = models.UUIDField()
    checkout_session = models.OneToOneField(
        CheckoutSession,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="order",
    )
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING_PAYMENT)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_address_snapshot = models.JSONField(default=dict, blank=True)
    payment_method = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def can_cancel(self):
        return self.status in {
            self.Status.PENDING_PAYMENT,
            self.Status.CONFIRMED,
            self.Status.PROCESSING,
        }

    def can_change_to(self, status):
        if status == self.status:
            return True
        return status in self.VALID_TRANSITIONS[self.status]

    def change_status(self, status):
        self.status = status
        self.save(update_fields=["status", "updated_at"])


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_id = models.UUIDField()
    sku = models.CharField(max_length=120)
    product_name = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=12, decimal_places=2)


class OrderStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    old_status = models.CharField(max_length=24, choices=Order.Status.choices, null=True, blank=True)
    new_status = models.CharField(max_length=24, choices=Order.Status.choices)
    changed_by = models.UUIDField(null=True, blank=True)
    note = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
