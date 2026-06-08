import json
import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.core import signing
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Address, CustomerProfile, UserAccount, UserSession


ACCESS_TOKEN_AGE_SECONDS = 900


def _body(request):
    if not request.body:
        return {}
    return json.loads(request.body.decode("utf-8"))


def _error(status, code, message, details=None):
    return JsonResponse(
        {"error": {"code": code, "message": message, "details": details or {}}},
        status=status,
    )


def _account_payload(user):
    return {
        "id": str(user.id),
        "email": user.email,
        "phone": user.phone,
        "status": user.status,
        "created_at": user.created_at.isoformat(),
    }


def _profile_payload(profile):
    return {
        "full_name": profile.full_name,
        "avatar_url": profile.avatar_url,
        "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
        "gender": profile.gender,
    }


def _address_payload(address):
    return {
        "id": str(address.id),
        "recipient_name": address.recipient_name,
        "recipient_phone": address.recipient_phone,
        "province": address.province,
        "district": address.district,
        "ward": address.ward,
        "detail": address.detail,
        "is_default": address.is_default,
        "created_at": address.created_at.isoformat(),
    }


def _issue_access_token(user):
    return signing.dumps(
        {
            "sub": str(user.id),
            "email": user.email,
            "token_type": "access",
            "iat": int(timezone.now().timestamp()),
        },
        salt="user-access-token",
    )


def _current_user(request):
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = signing.loads(
            token,
            salt="user-access-token",
            max_age=ACCESS_TOKEN_AGE_SECONDS,
        )
    except signing.BadSignature:
        return None
    if payload.get("token_type") != "access":
        return None
    return UserAccount.objects.filter(id=payload.get("sub")).first()


@csrf_exempt
def register(request):
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")

    data = _body(request)
    required = ["email", "phone", "password", "full_name"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return _error(400, "VALIDATION_ERROR", "Invalid data.", {"missing": missing})
    if UserAccount.objects.filter(email=data["email"]).exists():
        return _error(409, "EMAIL_ALREADY_EXISTS", "Email already exists.")
    if UserAccount.objects.filter(phone=data["phone"]).exists():
        return _error(409, "PHONE_ALREADY_EXISTS", "Phone already exists.")

    try:
        with transaction.atomic():
            user = UserAccount(email=data["email"], phone=data["phone"])
            user.set_password(data["password"])
            user.save()
            profile = CustomerProfile.objects.create(user=user, full_name=data["full_name"])
    except IntegrityError:
        return _error(409, "ACCOUNT_ALREADY_EXISTS", "Account already exists.")

    payload = _account_payload(user)
    payload["profile"] = {"full_name": profile.full_name}
    return JsonResponse(payload, status=201)


@csrf_exempt
def login(request):
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")

    data = _body(request)
    identifier = data.get("identifier")
    password = data.get("password")
    if not identifier or not password:
        return _error(400, "VALIDATION_ERROR", "Identifier and password are required.")

    user = UserAccount.objects.filter(email=identifier).first() or UserAccount.objects.filter(phone=identifier).first()
    if not user or not user.check_password(password):
        return _error(401, "INVALID_CREDENTIALS", "Invalid credentials.")
    if user.status == UserAccount.Status.LOCKED:
        return _error(423, "ACCOUNT_LOCKED", "Account is locked.")
    if not user.is_login_allowed():
        return _error(403, "ACCOUNT_NOT_ACTIVE", "Account is not active.")

    refresh_token = secrets.token_urlsafe(40)
    UserSession.objects.create(
        user=user,
        refresh_token_hash=make_password(refresh_token),
        device_info=data.get("device_info", ""),
        expires_at=timezone.now() + timedelta(days=30),
    )
    user.last_login_at = timezone.now()
    user.save(update_fields=["last_login_at", "updated_at"])

    return JsonResponse(
        {
            "token_type": "Bearer",
            "access_token": _issue_access_token(user),
            "refresh_token": refresh_token,
            "expires_in": ACCESS_TOKEN_AGE_SECONDS,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "phone": user.phone,
                "status": user.status,
                "full_name": user.profile.full_name,
            },
        }
    )


@csrf_exempt
def logout(request):
    user = _current_user(request)
    if not user:
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    data = _body(request)
    refresh_token = data.get("refresh_token")
    for session in user.sessions.filter(revoked_at__isnull=True):
        if refresh_token and check_password(refresh_token, session.refresh_token_hash):
            session.revoke()
            return HttpResponse(status=204)
    return _error(404, "SESSION_NOT_FOUND", "Session not found.")


@csrf_exempt
def profile(request):
    user = _current_user(request)
    if not user:
        return _error(401, "UNAUTHORIZED", "Unauthorized.")

    if request.method == "GET":
        return JsonResponse(
            {
                "id": str(user.id),
                "email": user.email,
                "phone": user.phone,
                "status": user.status,
                "profile": _profile_payload(user.profile),
                "addresses": [
                    _address_payload(address)
                    for address in user.addresses.filter(is_deleted=False).order_by("-is_default", "created_at")
                ],
            }
        )
    if request.method == "PATCH":
        data = _body(request)
        if data.get("phone") and UserAccount.objects.filter(phone=data["phone"]).exclude(id=user.id).exists():
            return _error(409, "PHONE_ALREADY_EXISTS", "Phone already exists.")
        if data.get("phone"):
            user.phone = data["phone"]
            user.save(update_fields=["phone", "updated_at"])
        profile_obj = user.profile
        for field in ["full_name", "date_of_birth", "gender", "avatar_url"]:
            if field in data:
                setattr(profile_obj, field, data[field] or None)
        profile_obj.save()
        return JsonResponse(
            {
                "id": str(user.id),
                "email": user.email,
                "phone": user.phone,
                "profile": _profile_payload(profile_obj),
                "updated_at": profile_obj.updated_at.isoformat(),
            }
        )
    return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")


@csrf_exempt
def addresses(request):
    user = _current_user(request)
    if not user:
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")

    data = _body(request)
    required = ["recipient_name", "recipient_phone", "province", "district", "ward", "detail"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return _error(400, "VALIDATION_ERROR", "Invalid address.", {"missing": missing})
    with transaction.atomic():
        if data.get("is_default"):
            user.addresses.filter(is_deleted=False).update(is_default=False)
        address = Address.objects.create(
            user=user,
            recipient_name=data["recipient_name"],
            recipient_phone=data["recipient_phone"],
            province=data["province"],
            district=data["district"],
            ward=data["ward"],
            detail=data["detail"],
            is_default=bool(data.get("is_default")),
        )
    return JsonResponse(_address_payload(address), status=201)


@csrf_exempt
def address_detail(request, address_id):
    user = _current_user(request)
    if not user:
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    if request.method != "DELETE":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    address = Address.objects.filter(id=address_id, is_deleted=False).first()
    if not address:
        return _error(404, "ADDRESS_NOT_FOUND", "Address not found.")
    if address.user_id != user.id:
        return _error(403, "ADDRESS_ACCESS_DENIED", "Address access denied.")
    address.soft_delete()
    return HttpResponse(status=204)
