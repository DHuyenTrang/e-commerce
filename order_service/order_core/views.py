import json
import uuid
from decimal import Decimal, InvalidOperation

from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import CheckoutSession, Order, OrderItem, OrderStatusHistory


def _body(request):
    if not request.body:
        return {}
    return json.loads(request.body.decode("utf-8"))


def _error(status, code, message, details=None):
    return JsonResponse({"error": {"code": code, "message": message, "details": details or {}}}, status=status)


def _user_id(request):
    raw = request.headers.get("X-User-Id")
    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except ValueError:
        return None


def _staff_id(request):
    raw = request.headers.get("X-Staff-Id")
    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except ValueError:
        return None


def _decimal(value):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValueError
    if number < 0:
        raise ValueError
    return number


def _money(value):
    amount = Decimal(value)
    return int(amount) if amount == amount.to_integral() else float(amount)


def _page(queryset, request):
    try:
        page = max(int(request.GET.get("page", 1)), 1)
        page_size = min(max(int(request.GET.get("page_size", 20)), 1), 100)
    except ValueError:
        page, page_size = 1, 20
    total = queryset.count()
    start = (page - 1) * page_size
    return queryset[start : start + page_size], page, page_size, total


def _order_code():
    today = timezone.now().strftime("%Y%m%d")
    return f"ORD-{today}-{uuid.uuid4().hex[:8].upper()}"


def _item_from_snapshot(item):
    required = ["product_id", "sku", "product_name", "unit_price", "quantity"]
    if any(item.get(field) in [None, ""] for field in required):
        raise ValueError
    product_id = uuid.UUID(str(item["product_id"]))
    unit_price = _decimal(item["unit_price"])
    quantity = int(item["quantity"])
    if quantity < 1:
        raise ValueError
    line_total = unit_price * quantity
    return {
        "product_id": product_id,
        "sku": item["sku"],
        "product_name": item["product_name"],
        "unit_price": unit_price,
        "quantity": quantity,
        "line_total": line_total,
    }


def _history_payload(history):
    if not history:
        return None
    return {
        "id": str(history.id),
        "old_status": history.old_status,
        "new_status": history.new_status,
        "changed_by": str(history.changed_by) if history.changed_by else None,
        "note": history.note,
        "changed_at": history.changed_at.isoformat(),
    }


def _item_payload(item):
    return {
        "id": str(item.id),
        "product_id": str(item.product_id),
        "sku": item.sku,
        "product_name": item.product_name,
        "unit_price": _money(item.unit_price),
        "quantity": item.quantity,
        "line_total": _money(item.line_total),
    }


def _order_summary(order):
    return {
        "id": str(order.id),
        "order_code": order.order_code,
        "status": order.status,
        "subtotal": _money(order.subtotal),
        "shipping_fee": _money(order.shipping_fee),
        "total_amount": _money(order.total_amount),
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
    }


def _order_detail(order):
    payload = _order_summary(order)
    payload.update(
        {
            "user_id": str(order.user_id),
            "shipping_address_snapshot": order.shipping_address_snapshot,
            "items": [_item_payload(item) for item in order.items.order_by("id")],
            "status_history": [_history_payload(history) for history in order.status_history.order_by("changed_at")],
        }
    )
    return payload


@csrf_exempt
def initiate_checkout(request):
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    user_id = _user_id(request)
    if not user_id:
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    data = _body(request)
    try:
        cart_id = uuid.UUID(str(data["cart_id"]))
        shipping_fee = _decimal(data.get("shipping_fee", 0))
        items = [_item_from_snapshot(item) for item in data.get("items", [])]
    except (KeyError, ValueError, TypeError):
        return _error(400, "VALIDATION_ERROR", "Invalid checkout data.")
    if not items:
        return _error(409, "EMPTY_CART", "Cart is empty.")
    subtotal = sum(item["line_total"] for item in items)
    session = CheckoutSession.objects.create(
        user_id=user_id,
        cart_id=cart_id,
        shipping_address_id=str(data.get("shipping_address_id", "")),
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        total_amount=subtotal + shipping_fee,
        shipping_address_snapshot=data.get("shipping_address_snapshot", {}),
        items_snapshot=[
            {
                **item,
                "product_id": str(item["product_id"]),
                "unit_price": str(item["unit_price"]),
                "line_total": str(item["line_total"]),
            }
            for item in items
        ],
        expires_at=timezone.now() + timezone.timedelta(minutes=30),
    )
    return JsonResponse(
        {
            "checkout_id": str(session.id),
            "subtotal": _money(session.subtotal),
            "shipping_fee": _money(session.shipping_fee),
            "total_amount": _money(session.total_amount),
            "expires_at": session.expires_at.isoformat(),
        },
        status=201,
    )


@csrf_exempt
def place_order(request):
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    user_id = _user_id(request)
    if not user_id:
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    data = _body(request)
    checkout = CheckoutSession.objects.filter(id=data.get("checkout_id"), user_id=user_id).first()
    if not checkout:
        return _error(404, "CHECKOUT_NOT_FOUND", "Checkout session not found.")
    if not checkout.is_usable():
        return _error(409, "CHECKOUT_EXPIRED", "Checkout session has expired.")
    payment_method = data.get("payment_method", "")
    status = Order.Status.CONFIRMED if payment_method == "COD" else Order.Status.PENDING_PAYMENT
    try:
        with transaction.atomic():
            order = Order.objects.create(
                order_code=_order_code(),
                user_id=user_id,
                checkout_session=checkout,
                status=status,
                subtotal=checkout.subtotal,
                shipping_fee=checkout.shipping_fee,
                total_amount=checkout.total_amount,
                shipping_address_snapshot=checkout.shipping_address_snapshot,
                payment_method=payment_method,
            )
            OrderItem.objects.bulk_create(
                [
                    OrderItem(
                        order=order,
                        product_id=item["product_id"],
                        sku=item["sku"],
                        product_name=item["product_name"],
                        unit_price=Decimal(item["unit_price"]),
                        quantity=item["quantity"],
                        line_total=Decimal(item["line_total"]),
                    )
                    for item in checkout.items_snapshot
                ]
            )
            OrderStatusHistory.objects.create(order=order, old_status=None, new_status=status, changed_by=user_id, note="Order placed")
            checkout.mark_placed()
    except IntegrityError:
        return _error(409, "ORDER_ALREADY_PLACED", "Checkout session already placed.")
    return JsonResponse(
        {
            "id": str(order.id),
            "order_code": order.order_code,
            "status": order.status,
            "total_amount": _money(order.total_amount),
        },
        status=201,
    )


def list_user_orders(request):
    if request.method != "GET":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    user_id = _user_id(request)
    if not user_id:
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    queryset = Order.objects.filter(user_id=user_id).order_by("-created_at")
    if request.GET.get("status"):
        queryset = queryset.filter(status=request.GET["status"])
    items, page, page_size, total = _page(queryset, request)
    return JsonResponse({"items": [_order_summary(order) for order in items], "page": page, "page_size": page_size, "total": total})


def get_order_detail(request, order_id):
    if request.method != "GET":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    user_id = _user_id(request)
    if not user_id:
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    order = Order.objects.filter(id=order_id, user_id=user_id).prefetch_related("items", "status_history").first()
    if not order:
        return _error(404, "ORDER_NOT_FOUND", "Order not found.")
    return JsonResponse(_order_detail(order))


@csrf_exempt
def cancel_order_request(request, order_id):
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    user_id = _user_id(request)
    if not user_id:
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    order = Order.objects.filter(id=order_id, user_id=user_id).first()
    if not order:
        return _error(404, "ORDER_NOT_FOUND", "Order not found.")
    if not order.can_cancel():
        return _error(409, "ORDER_CANNOT_BE_CANCELLED", "Order cannot be cancelled.")
    data = _body(request)
    old_status = order.status
    order.change_status(Order.Status.CANCEL_REQUESTED)
    history = OrderStatusHistory.objects.create(
        order=order,
        old_status=old_status,
        new_status=Order.Status.CANCEL_REQUESTED,
        changed_by=user_id,
        note=data.get("reason", ""),
    )
    payload = _order_summary(order)
    payload["latest_status_history"] = _history_payload(history)
    return JsonResponse(payload)


def list_all_orders(request):
    if request.method != "GET":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    if not _staff_id(request):
        return _error(403, "FORBIDDEN", "Admin permission required.")
    queryset = Order.objects.all().order_by("-created_at")
    if request.GET.get("status"):
        queryset = queryset.filter(status=request.GET["status"])
    items, page, page_size, total = _page(queryset, request)
    return JsonResponse({"items": [_order_summary(order) for order in items], "page": page, "page_size": page_size, "total": total})


@csrf_exempt
def update_order_status(request, order_id):
    if request.method != "PATCH":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    staff_id = _staff_id(request)
    if not staff_id:
        return _error(403, "FORBIDDEN", "Admin permission required.")
    order = Order.objects.filter(id=order_id).first()
    if not order:
        return _error(404, "ORDER_NOT_FOUND", "Order not found.")
    data = _body(request)
    status = data.get("status")
    if status not in Order.Status.values:
        return _error(400, "VALIDATION_ERROR", "Invalid order status.")
    if not order.can_change_to(status):
        return _error(409, "INVALID_ORDER_STATUS_TRANSITION", "Invalid order status transition.")
    old_status = order.status
    order.change_status(status)
    history = OrderStatusHistory.objects.create(
        order=order,
        old_status=old_status,
        new_status=status,
        changed_by=staff_id,
        note=data.get("note", ""),
    )
    payload = _order_summary(order)
    payload["latest_status_history"] = _history_payload(history)
    return JsonResponse(payload)
