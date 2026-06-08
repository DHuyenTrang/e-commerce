import uuid

from django.db import models


class ActiveStatus(models.TextChoices):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True, related_name="children")
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=ActiveStatus.choices, default=ActiveStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Brand(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    logo_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=ActiveStatus.choices, default=ActiveStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    status = models.CharField(max_length=16, choices=ActiveStatus.choices, default=ActiveStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Product(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT"
        ACTIVE = "ACTIVE"
        INACTIVE = "INACTIVE"
        DELETED = "DELETED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    sku = models.CharField(max_length=120, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    original_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    attributes = models.JSONField(default=dict, blank=True)
    tags = models.ManyToManyField(Tag, through="ProductTag", related_name="products")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_visible(self):
        return self.status == self.Status.ACTIVE

    def update_stock(self, quantity):
        self.stock_quantity = quantity
        self.save(update_fields=["stock_quantity", "updated_at"])

    def deactivate(self):
        self.status = self.Status.INACTIVE
        self.save(update_fields=["status", "updated_at"])


class Image(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    url = models.URLField()
    alt_text = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_thumbnail = models.BooleanField(default=False)


class ProductTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "tag"], name="unique_product_tag"),
        ]
