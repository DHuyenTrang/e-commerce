import uuid
from urllib.error import URLError

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .auth import parse_bearer_token
from . import proxy
from .rate_limit import check_rate_limit
from .routing import resolve_route


def gateway_error(status, code, message, request_id):
    return JsonResponse(
        {"error": {"code": code, "message": message, "request_id": request_id}},
        status=status,
    )


def _request_id(request):
    return request.headers.get("X-Request-Id") or f"req-{uuid.uuid4()}"


def _client_ip(request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _headers_for_upstream(request, request_id, identity):
    headers = {
        "X-Request-Id": request_id,
        "X-Forwarded-For": _client_ip(request),
    }
    content_type = request.headers.get("Content-Type")
    if content_type:
        headers["Content-Type"] = content_type
    authorization = request.headers.get("Authorization")
    if authorization:
        headers["Authorization"] = authorization
    if identity:
        if identity.subject_type == "user":
            headers["X-User-Id"] = identity.subject_id
        if identity.subject_type == "staff":
            headers["X-Staff-Id"] = identity.subject_id
        if identity.roles:
            headers["X-Roles"] = ",".join(identity.roles)
        if identity.permissions:
            headers["X-Permissions"] = ",".join(identity.permissions)
    return headers


@csrf_exempt
def gateway_entrypoint(request, path):
    full_path = "/" + path
    request_id = _request_id(request)

    route = resolve_route(full_path)
    if not route:
        return gateway_error(404, "ROUTE_NOT_FOUND", "Route not found.", request_id)

    rate_limit_key = f"{_client_ip(request)}:{full_path}"
    if not check_rate_limit(rate_limit_key):
        return gateway_error(429, "RATE_LIMIT_EXCEEDED", "Rate limit exceeded.", request_id)

    required_permission = route.required_permission(full_path, request.method)
    is_public = route.is_public(full_path) and required_permission is None
    identity = None
    if not is_public:
        identity = parse_bearer_token(request.headers.get("Authorization"))
        if not identity:
            return gateway_error(401, "UNAUTHORIZED", "Missing or invalid token.", request_id)
    if required_permission:
        if not identity or identity.subject_type != "staff":
            return gateway_error(403, "FORBIDDEN", "Permission denied.", request_id)
        if required_permission not in identity.permissions:
            return gateway_error(403, "FORBIDDEN", "Permission denied.", request_id)

    try:
        upstream = proxy.forward_request(
            service_name=route.service_name,
            method=request.method,
            path=full_path,
            query_string=request.META.get("QUERY_STRING", ""),
            headers=_headers_for_upstream(request, request_id, identity),
            body=request.body,
        )
    except URLError:
        return gateway_error(502, "BAD_GATEWAY", "Target service is unavailable.", request_id)

    response = HttpResponse(
        upstream["content"],
        status=upstream["status_code"],
        content_type=upstream["headers"].get("Content-Type", "application/json"),
    )
    response["X-Request-Id"] = request_id
    return response
