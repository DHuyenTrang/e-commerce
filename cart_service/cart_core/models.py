import uuid

from django.db import models


class Cart(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE"
        CHECKED_OUT = "CHECKED_OUT"
        ABANDONED = "ABANDONED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(null=True, blank=True)
    guest_session_id = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_active(self):
        return self.status == self.Status.ACTIVE


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product_id = models.UUIDField()
    sku = models.CharField(max_length=120)
    quantity = models.PositiveIntegerField()
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_quantity(self, quantity):
        self.quantity = quantity
        self.save(update_fields=["quantity", "updated_at"])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["cart", "product_id", "sku"], name="unique_cart_product_sku"),
        ]
