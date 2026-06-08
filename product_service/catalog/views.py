import json
from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import ActiveStatus, Brand, Category, Image, Product, ProductTag, Tag


def _body(request):
    if not request.body:
        return {}
    return json.loads(request.body.decode("utf-8"))


def _error(status, code, message, details=None):
    return JsonResponse(
        {"error": {"code": code, "message": message, "details": details or {}}},
        status=status,
    )


def _require_auth(request):
    return request.headers.get("Authorization", "").startswith("Bearer ")


def _decimal(value, field):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValueError(field)
    if number < 0:
        raise ValueError(field)
    return number


def _metadata_payload(instance):
    payload = {
        "id": str(instance.id),
        "name": instance.name,
        "slug": instance.slug,
        "status": instance.status,
    }
    if isinstance(instance, Category):
        payload["parent_id"] = str(instance.parent_id) if instance.parent_id else None
    if isinstance(instance, Brand):
        payload["logo_url"] = instance.logo_url
    return payload


def _thumbnail(product):
    image = product.images.filter(is_thumbnail=True).order_by("sort_order").first()
    return image.url if image else None


def _summary(product):
    return {
        "id": str(product.id),
        "name": product.name,
        "slug": product.slug,
        "price": int(product.price) if product.price == product.price.to_integral() else float(product.price),
        "thumbnail": _thumbnail(product),
        "category": {"id": str(product.category_id), "name": product.category.name},
        "brand": {"id": str(product.brand_id), "name": product.brand.name},
        "stock_quantity": product.stock_quantity,
    }


def _detail(product):
    payload = _summary(product)
    payload.update(
        {
            "sku": product.sku,
            "original_price": int(product.original_price)
            if product.original_price and product.original_price == product.original_price.to_integral()
            else (float(product.original_price) if product.original_price is not None else None),
            "tags": list(product.tags.order_by("slug").values_list("slug", flat=True)),
            "images": [
                {
                    "url": image.url,
                    "alt_text": image.alt_text,
                    "sort_order": image.sort_order,
                    "is_thumbnail": image.is_thumbnail,
                }
                for image in product.images.order_by("sort_order")
            ],
            "attributes": product.attributes,
        }
    )
    return payload


def _active_products():
    return Product.objects.select_related("category", "brand").filter(status=Product.Status.ACTIVE)


def list_products(request):
    if request.method != "GET":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    queryset = _active_products().order_by("-created_at")
    category_slug = request.GET.get("category")
    if category_slug:
        category = Category.objects.filter(slug=category_slug, status=ActiveStatus.ACTIVE).first()
        if not category:
            return _error(404, "CATEGORY_NOT_FOUND", "Category not found.")
        queryset = queryset.filter(category=category)
    items = [_summary(product) for product in queryset]
    return JsonResponse({"items": items, "page": 1, "page_size": len(items) or 20, "total": len(items)})


def search_products(request):
    if request.method != "GET":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    keyword = request.GET.get("q", "").strip()
    if not keyword:
        return _error(400, "VALIDATION_ERROR", "Search keyword is required.")
    queryset = (
        _active_products()
        .filter(
            Q(name__icontains=keyword)
            | Q(sku__icontains=keyword)
            | Q(brand__name__icontains=keyword)
            | Q(tags__name__icontains=keyword)
            | Q(tags__slug__icontains=keyword)
        )
        .distinct()
        .order_by("-created_at")
    )
    items = [_summary(product) for product in queryset]
    return JsonResponse({"items": items, "page": 1, "page_size": len(items) or 20, "total": len(items)})


def product_detail(request, product_id_or_slug):
    if request.method != "GET":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    query = Q(slug=product_id_or_slug)
    try:
        query |= Q(id=UUID(product_id_or_slug))
    except ValueError:
        pass
    product = _active_products().filter(query).first()
    if not product:
        return _error(404, "PRODUCT_NOT_FOUND", "Product not found.")
    return JsonResponse(_detail(product))


@csrf_exempt
def manage_metadata(request, metadata_type):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    data = _body(request)
    model_by_type = {"category": Category, "brand": Brand, "tag": Tag}
    model = model_by_type.get(metadata_type)
    if not model:
        return _error(400, "VALIDATION_ERROR", "Invalid metadata type.")

    if request.method == "PATCH":
        instance = None
        if data.get("id"):
            instance = model.objects.filter(id=data["id"]).first()
        elif data.get("slug"):
            instance = model.objects.filter(slug=data["slug"]).first()
        if not instance:
            return _error(404, f"{metadata_type.upper()}_NOT_FOUND", "Metadata not found.")
        if data.get("slug") and model.objects.filter(slug=data["slug"]).exclude(id=instance.id).exists():
            return _error(409, "SLUG_ALREADY_EXISTS", "Slug already exists.")
        for field in ["name", "slug", "description", "status"]:
            if field in data:
                setattr(instance, field, data[field])
        if isinstance(instance, Brand) and "logo_url" in data:
            instance.logo_url = data["logo_url"]
        if isinstance(instance, Category) and "parent_id" in data:
            instance.parent = Category.objects.filter(id=data["parent_id"]).first() if data["parent_id"] else None
        instance.save()
        return JsonResponse(_metadata_payload(instance))

    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    if not data.get("name") or not data.get("slug"):
        return _error(400, "VALIDATION_ERROR", "Name and slug are required.")
    try:
        if model is Category:
            parent = None
            if data.get("parent_id"):
                parent = Category.objects.filter(id=data["parent_id"], status=ActiveStatus.ACTIVE).first()
                if not parent:
                    return _error(404, "CATEGORY_NOT_FOUND", "Parent category not found.")
            instance = Category.objects.create(
                name=data["name"],
                slug=data["slug"],
                parent=parent,
                description=data.get("description", ""),
                status=data.get("status", ActiveStatus.ACTIVE),
            )
        elif model is Brand:
            instance = Brand.objects.create(
                name=data["name"],
                slug=data["slug"],
                logo_url=data.get("logo_url", ""),
                description=data.get("description", ""),
                status=data.get("status", ActiveStatus.ACTIVE),
            )
        else:
            instance = Tag.objects.create(
                name=data["name"],
                slug=data["slug"],
                status=data.get("status", ActiveStatus.ACTIVE),
            )
    except IntegrityError:
        return _error(409, "SLUG_ALREADY_EXISTS", "Slug already exists.")
    return JsonResponse(_metadata_payload(instance), status=201)


@csrf_exempt
def admin_products(request):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    data = _body(request)
    required = ["name", "slug", "sku", "category_id", "brand_id", "price", "stock_quantity"]
    missing = [field for field in required if data.get(field) in [None, ""]]
    if missing:
        return _error(400, "VALIDATION_ERROR", "Invalid product.", {"missing": missing})
    if Product.objects.filter(sku=data["sku"]).exists():
        return _error(409, "SKU_ALREADY_EXISTS", "SKU already exists.")
    if Product.objects.filter(slug=data["slug"]).exists():
        return _error(409, "SLUG_ALREADY_EXISTS", "Slug already exists.")
    category = Category.objects.filter(id=data["category_id"], status=ActiveStatus.ACTIVE).first()
    if not category:
        return _error(404, "CATEGORY_NOT_FOUND", "Category not found.")
    brand = Brand.objects.filter(id=data["brand_id"], status=ActiveStatus.ACTIVE).first()
    if not brand:
        return _error(404, "BRAND_NOT_FOUND", "Brand not found.")
    tag_ids = data.get("tag_ids", [])
    if Tag.objects.filter(id__in=tag_ids, status=ActiveStatus.ACTIVE).count() != len(set(tag_ids)):
        return _error(404, "TAG_NOT_FOUND", "Tag not found.")
    try:
        price = _decimal(data["price"], "price")
        original_price = _decimal(data["original_price"], "original_price") if data.get("original_price") is not None else None
        stock_quantity = int(data["stock_quantity"])
        if stock_quantity < 0 or (original_price is not None and original_price < price):
            raise ValueError("stock_quantity")
    except (ValueError, TypeError):
        return _error(400, "VALIDATION_ERROR", "Invalid price or stock quantity.")
    with transaction.atomic():
        product = Product.objects.create(
            name=data["name"],
            slug=data["slug"],
            sku=data["sku"],
            category=category,
            brand=brand,
            price=price,
            original_price=original_price,
            stock_quantity=stock_quantity,
            status=data.get("status", Product.Status.DRAFT),
            attributes=data.get("attributes", {}),
        )
        ProductTag.objects.bulk_create([ProductTag(product=product, tag_id=tag_id) for tag_id in tag_ids])
        _replace_images(product, data.get("images", []))
    return JsonResponse(_detail(product), status=201)


def _replace_images(product, images):
    product.images.all().delete()
    image_objects = []
    for index, image in enumerate(images):
        image_objects.append(
            Image(
                product=product,
                url=image["url"],
                alt_text=image.get("alt_text", ""),
                sort_order=image.get("sort_order", index),
                is_thumbnail=bool(image.get("is_thumbnail")),
            )
        )
    Image.objects.bulk_create(image_objects)


@csrf_exempt
def admin_product_detail(request, product_id):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    product = Product.objects.filter(id=product_id).first()
    if not product:
        return _error(404, "PRODUCT_NOT_FOUND", "Product not found.")
    if request.method == "DELETE":
        product.deactivate()
        return HttpResponse(status=204)
    if request.method == "PATCH":
        data = _body(request)
        for field in ["name", "slug", "sku", "status", "attributes"]:
            if field in data:
                setattr(product, field, data[field])
        if "price" in data:
            product.price = _decimal(data["price"], "price")
        if "original_price" in data:
            product.original_price = _decimal(data["original_price"], "original_price") if data["original_price"] is not None else None
        product.save()
        if "tag_ids" in data:
            ProductTag.objects.filter(product=product).delete()
            ProductTag.objects.bulk_create([ProductTag(product=product, tag_id=tag_id) for tag_id in data["tag_ids"]])
        if "images" in data:
            _replace_images(product, data["images"])
        return JsonResponse(_detail(product))
    return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")


@csrf_exempt
def admin_product_stock(request, product_id):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    if request.method != "PATCH":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    product = Product.objects.filter(id=product_id).first()
    if not product:
        return _error(404, "PRODUCT_NOT_FOUND", "Product not found.")
    try:
        quantity = int(_body(request).get("stock_quantity"))
    except (TypeError, ValueError):
        return _error(400, "VALIDATION_ERROR", "Invalid stock quantity.")
    if quantity < 0:
        return _error(400, "VALIDATION_ERROR", "Invalid stock quantity.")
    product.update_stock(quantity)
    return JsonResponse(
        {
            "id": str(product.id),
            "sku": product.sku,
            "stock_quantity": product.stock_quantity,
            "updated_at": product.updated_at.isoformat(),
        }
    )
