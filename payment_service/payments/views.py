import json
import uuid
from decimal import Decimal, InvalidOperation

from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import PaymentGatewayCallback, PaymentMethod, PaymentTransaction


def _body(request):
    if not request.body:
        return {}
    return json.loads(request.body.decode("utf-8"))


def _error(status, code, message, details=None):
    return JsonResponse({"error": {"code": code, "message": message, "details": details or {}}}, status=status)


def _require_auth(request):
    return request.headers.get("Authorization", "").startswith("Bearer ")


def _decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValueError


def _money(value):
    amount = Decimal(value)
    return int(amount) if amount == amount.to_integral() else float(amount)


def _method_payload(method):
    return {"id": str(method.id), "code": method.code, "name": method.name, "provider": method.provider, "is_active": method.is_active}


def _transaction_payload(transaction):
    return {
        "id": str(transaction.id),
        "order_id": str(transaction.order_id),
        "transaction_code": transaction.transaction_code,
        "amount": _money(transaction.amount),
        "currency": transaction.currency,
        "payment_method_code": transaction.payment_method.code,
        "status": transaction.status,
        "gateway_reference": transaction.gateway_reference,
    }


@csrf_exempt
def admin_methods(request):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    data = _body(request)
    if not data.get("code") or not data.get("name") or not data.get("provider"):
        return _error(400, "VALIDATION_ERROR", "Invalid payment method.")
    try:
        method = PaymentMethod.objects.create(
            code=data["code"],
            name=data["name"],
            provider=data["provider"],
            is_active=bool(data.get("is_active", True)),
            config=data.get("config", {}),
        )
    except IntegrityError:
        return _error(409, "PAYMENT_METHOD_ALREADY_EXISTS", "Payment method already exists.")
    return JsonResponse(_method_payload(method), status=201)


def methods(request):
    if request.method != "GET":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    return JsonResponse({"items": [_method_payload(method) for method in PaymentMethod.objects.filter(is_active=True).order_by("code")]})


@csrf_exempt
def transactions(request):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    data = _body(request)
    try:
        order_id = uuid.UUID(str(data.get("order_id")))
        amount = _decimal(data.get("amount"))
    except ValueError:
        return _error(400, "VALIDATION_ERROR", "Invalid payment transaction.")
    if amount <= 0:
        return _error(400, "VALIDATION_ERROR", "Invalid payment amount.")
    method = PaymentMethod.objects.filter(code=data.get("payment_method_code"), is_active=True).first()
    if not method:
        return _error(404, "PAYMENT_METHOD_NOT_FOUND", "Payment method not found.")
    transaction = PaymentTransaction.objects.create(
        order_id=order_id,
        transaction_code=data.get("transaction_code") or f"PAY-{uuid.uuid4().hex[:16].upper()}",
        amount=amount,
        currency=data.get("currency", "VND"),
        payment_method=method,
        gateway_reference=data.get("gateway_reference", ""),
    )
    payload = _transaction_payload(transaction)
    payload["payment_url"] = data.get("return_url", "")
    return JsonResponse(payload, status=201)


@csrf_exempt
def callbacks(request, provider):
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    data = _body(request)
    if data.get("signature_valid") is False:
        return _error(422, "INVALID_GATEWAY_SIGNATURE", "Invalid gateway signature.")
    transaction = None
    if data.get("transaction_id"):
        transaction = PaymentTransaction.objects.filter(id=data["transaction_id"]).first()
    if not transaction and data.get("transaction_code"):
        transaction = PaymentTransaction.objects.filter(transaction_code=data["transaction_code"]).first()
    if not transaction:
        return _error(404, "PAYMENT_TRANSACTION_NOT_FOUND", "Payment transaction not found.")
    PaymentGatewayCallback.objects.create(
        transaction=transaction,
        provider=provider.upper(),
        payload=data,
        signature_valid=bool(data.get("signature_valid", True)),
    )
    status = data.get("status")
    if status == PaymentTransaction.Status.SUCCESS:
        transaction.mark_success(data.get("gateway_reference", transaction.gateway_reference))
    elif status == PaymentTransaction.Status.FAILED:
        transaction.mark_failed(data.get("reason", "Payment failed."))
    return JsonResponse(_transaction_payload(transaction))


def transaction_status(request, transaction_id):
    if request.method != "GET":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    transaction = PaymentTransaction.objects.filter(id=transaction_id).select_related("payment_method").first()
    if not transaction:
        return _error(404, "PAYMENT_TRANSACTION_NOT_FOUND", "Payment transaction not found.")
    return JsonResponse(
        {
            "transaction_id": str(transaction.id),
            "order_id": str(transaction.order_id),
            "status": transaction.status,
            "gateway_reference": transaction.gateway_reference,
            "paid_at": transaction.paid_at.isoformat() if transaction.paid_at else None,
        }
    )
