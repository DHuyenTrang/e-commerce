import json
import uuid
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Carrier, Shipment, ShippingRate, TrackingEvent


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
    rounded = Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(rounded)


def _carrier_payload(carrier):
    return {"id": str(carrier.id), "code": carrier.code, "name": carrier.name, "is_active": carrier.is_active}


def _shipment_payload(shipment):
    return {
        "id": str(shipment.id),
        "order_id": str(shipment.order_id),
        "carrier_code": shipment.carrier.code,
        "tracking_number": shipment.tracking_number,
        "status": shipment.status,
        "shipping_fee": _money(shipment.shipping_fee),
        "receiver_address_snapshot": shipment.receiver_address_snapshot,
    }


def _event_payload(event):
    return {
        "id": str(event.id),
        "status": event.status,
        "location": event.location,
        "description": event.description,
        "occurred_at": event.occurred_at.isoformat(),
    }


@csrf_exempt
def carriers(request):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    data = _body(request)
    if request.method == "POST":
        if not data.get("code") or not data.get("name"):
            return _error(400, "VALIDATION_ERROR", "Carrier code and name are required.")
        try:
            carrier = Carrier.objects.create(
                code=data["code"],
                name=data["name"],
                is_active=bool(data.get("is_active", True)),
                config=data.get("config", {}),
            )
        except IntegrityError:
            return _error(409, "CARRIER_ALREADY_EXISTS", "Carrier already exists.")
        return JsonResponse(_carrier_payload(carrier), status=201)
    if request.method == "PATCH":
        carrier = Carrier.objects.filter(code=data.get("code")).first()
        if not carrier:
            return _error(404, "CARRIER_NOT_FOUND", "Carrier not found.")
        for field in ["name", "is_active", "config"]:
            if field in data:
                setattr(carrier, field, data[field])
        carrier.save()
        return JsonResponse(_carrier_payload(carrier))
    return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")


@csrf_exempt
def rates(request):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    data = _body(request)
    carrier = Carrier.objects.filter(code=data.get("carrier_code")).first()
    if not carrier:
        return _error(404, "CARRIER_NOT_FOUND", "Carrier not found.")
    try:
        rate = ShippingRate.objects.create(
            carrier=carrier,
            province=data["province"],
            base_fee=_decimal(data["base_fee"]),
            fee_per_kg=_decimal(data["fee_per_kg"]),
            estimated_days=int(data.get("estimated_days", 3)),
        )
    except (KeyError, ValueError, IntegrityError):
        return _error(400, "VALIDATION_ERROR", "Invalid shipping rate.")
    return JsonResponse(
        {
            "id": str(rate.id),
            "carrier_code": carrier.code,
            "province": rate.province,
            "base_fee": _money(rate.base_fee),
            "fee_per_kg": _money(rate.fee_per_kg),
            "estimated_days": rate.estimated_days,
        },
        status=201,
    )


@csrf_exempt
def fees(request):
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    data = _body(request)
    try:
        weight_kg = _decimal(data.get("weight_kg"))
    except ValueError:
        return _error(400, "VALIDATION_ERROR", "Invalid weight.")
    if weight_kg <= 0:
        return _error(400, "VALIDATION_ERROR", "Invalid weight.")
    carrier = Carrier.objects.filter(code=data.get("carrier_code"), is_active=True).first()
    if not carrier:
        return _error(404, "CARRIER_NOT_FOUND", "Carrier not found.")
    rate = ShippingRate.objects.filter(carrier=carrier, province=data.get("province")).first()
    if not rate:
        return _error(404, "SHIPPING_RATE_NOT_FOUND", "Shipping rate not found.")
    fee = rate.base_fee + (rate.fee_per_kg * weight_kg)
    return JsonResponse({"carrier_code": carrier.code, "shipping_fee": _money(fee), "estimated_days": rate.estimated_days})


@csrf_exempt
def shipments(request):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    data = _body(request)
    carrier = Carrier.objects.filter(code=data.get("carrier_code"), is_active=True).first()
    if not carrier:
        return _error(404, "CARRIER_NOT_FOUND", "Carrier not found.")
    try:
        order_id = uuid.UUID(str(data["order_id"]))
        shipping_fee = _decimal(data["shipping_fee"])
    except (KeyError, ValueError):
        return _error(400, "VALIDATION_ERROR", "Invalid shipment data.")
    shipment = Shipment.objects.create(
        order_id=order_id,
        carrier=carrier,
        tracking_number=data.get("tracking_number") or f"{carrier.code}-{uuid.uuid4().hex[:12].upper()}",
        shipping_fee=shipping_fee,
        receiver_address_snapshot=data.get("receiver_address_snapshot", {}),
    )
    return JsonResponse(_shipment_payload(shipment), status=201)


@csrf_exempt
def shipment_tracking(request, shipment_id):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    if request.method != "PATCH":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    shipment = Shipment.objects.filter(id=shipment_id).first()
    if not shipment:
        return _error(404, "SHIPMENT_NOT_FOUND", "Shipment not found.")
    data = _body(request)
    status = data.get("status")
    if status not in Shipment.Status.values:
        return _error(400, "VALIDATION_ERROR", "Invalid shipment status.")
    shipment.change_status(status)
    event = TrackingEvent.objects.create(
        shipment=shipment,
        status=status,
        location=data.get("location", ""),
        description=data.get("description", ""),
    )
    payload = _shipment_payload(shipment)
    payload["event"] = _event_payload(event)
    return JsonResponse(payload)


def track(request, tracking_number):
    if request.method != "GET":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    shipment = Shipment.objects.filter(tracking_number=tracking_number).select_related("carrier").first()
    if not shipment:
        return _error(404, "SHIPMENT_NOT_FOUND", "Shipment not found.")
    payload = _shipment_payload(shipment)
    payload["events"] = [_event_payload(event) for event in shipment.events.order_by("-occurred_at")]
    return JsonResponse(payload)
