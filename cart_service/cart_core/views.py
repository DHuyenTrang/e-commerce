import json
import uuid

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Cart, CartItem


def _body(request):
    if not request.body:
        return {}
    return json.loads(request.body.decode("utf-8"))


def _error(status, code, message, details=None):
    return JsonResponse(
        {"error": {"code": code, "message": message, "details": details or {}}},
        status=status,
    )


def _cart_identity(request):
    user_id = request.headers.get("X-User-Id")
    guest_session_id = request.headers.get("X-Guest-Session-Id", "anonymous")
    return user_id, guest_session_id


def _get_or_create_cart(request):
    user_id, guest_session_id = _cart_identity(request)
    if user_id:
        cart, _ = Cart.objects.get_or_create(user_id=user_id, status=Cart.Status.ACTIVE, defaults={"guest_session_id": ""})
        return cart
    cart, _ = Cart.objects.get_or_create(
        guest_session_id=guest_session_id,
        status=Cart.Status.ACTIVE,
        user_id__isnull=True,
    )
    return cart


def _item_payload(item):
    return {
        "id": str(item.id),
        "product_id": str(item.product_id),
        "sku": item.sku,
        "quantity": item.quantity,
    }


def _cart_payload(cart):
    return {
        "id": str(cart.id),
        "status": cart.status,
        "items": [_item_payload(item) for item in cart.items.order_by("added_at")],
    }


@csrf_exempt
def cart_detail(request):
    if request.method != "GET":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    return JsonResponse(_cart_payload(_get_or_create_cart(request)))


@csrf_exempt
def cart_items(request):
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    data = _body(request)
    required = ["product_id", "sku", "quantity"]
    missing = [field for field in required if data.get(field) in [None, ""]]
    if missing:
        return _error(400, "VALIDATION_ERROR", "Invalid cart item.", {"missing": missing})
    try:
        product_id = uuid.UUID(str(data["product_id"]))
        quantity = int(data["quantity"])
    except (TypeError, ValueError):
        return _error(400, "VALIDATION_ERROR", "Invalid cart item.")
    if quantity < 1:
        return _error(409, "INVALID_QUANTITY", "Quantity must be greater than zero.")
    cart = _get_or_create_cart(request)
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product_id=product_id,
        sku=data["sku"],
        defaults={"quantity": quantity},
    )
    if not created:
        item.update_quantity(item.quantity + quantity)
    return JsonResponse(_item_payload(item), status=201)


@csrf_exempt
def cart_item_detail(request, item_id):
    cart = _get_or_create_cart(request)
    item = CartItem.objects.filter(id=item_id, cart=cart).first()
    if not item:
        return _error(404, "CART_ITEM_NOT_FOUND", "Cart item not found.")
    if request.method == "PATCH":
        try:
            quantity = int(_body(request).get("quantity"))
        except (TypeError, ValueError):
            return _error(400, "VALIDATION_ERROR", "Invalid quantity.")
        if quantity < 1:
            return _error(409, "INVALID_QUANTITY", "Quantity must be greater than zero.")
        item.update_quantity(quantity)
        return JsonResponse(_item_payload(item))
    if request.method == "DELETE":
        item.delete()
        return HttpResponse(status=204)
    return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
