import json
import uuid

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import CommentModeration, CommentReply, Review, VisibleStatus


def _body(request):
    if not request.body:
        return {}
    return json.loads(request.body.decode("utf-8"))


def _error(status, code, message, details=None):
    return JsonResponse({"error": {"code": code, "message": message, "details": details or {}}}, status=status)


def _require_auth(request):
    return request.headers.get("Authorization", "").startswith("Bearer ")


def _uuid(value, field):
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        raise ValueError(field)


def _review_payload(review, include_replies=False):
    payload = {
        "id": str(review.id),
        "product_id": str(review.product_id),
        "user_id": str(review.user_id),
        "order_id": str(review.order_id) if review.order_id else None,
        "rating": review.rating,
        "content": review.content,
        "status": review.status,
        "created_at": review.created_at.isoformat(),
    }
    if include_replies:
        payload["replies"] = [
            _reply_payload(reply)
            for reply in review.replies.filter(status=VisibleStatus.VISIBLE).order_by("created_at")
        ]
    return payload


def _reply_payload(reply):
    return {
        "id": str(reply.id),
        "review_id": str(reply.review_id),
        "staff_id": str(reply.staff_id),
        "content": reply.content,
        "status": reply.status,
        "created_at": reply.created_at.isoformat(),
    }


@csrf_exempt
def reviews(request):
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    data = _body(request)
    try:
        product_id = _uuid(data.get("product_id"), "product_id")
        user_id = _uuid(request.headers.get("X-User-Id"), "user_id")
        order_id = _uuid(data["order_id"], "order_id") if data.get("order_id") else None
        rating = int(data.get("rating"))
    except (TypeError, ValueError):
        return _error(400, "VALIDATION_ERROR", "Invalid review data.")
    if rating < 1 or rating > 5 or not data.get("content"):
        return _error(400, "VALIDATION_ERROR", "Invalid review data.")
    review = Review.objects.create(
        product_id=product_id,
        user_id=user_id,
        order_id=order_id,
        rating=rating,
        content=data["content"],
    )
    return JsonResponse(_review_payload(review), status=201)


def product_reviews(request, product_id):
    if request.method != "GET":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    try:
        product_uuid = uuid.UUID(str(product_id))
    except ValueError:
        return _error(400, "VALIDATION_ERROR", "Invalid product id.")
    queryset = Review.objects.filter(product_id=product_uuid, status=VisibleStatus.VISIBLE).order_by("-created_at")
    items = [_review_payload(review, include_replies=True) for review in queryset]
    return JsonResponse({"items": items, "total": len(items)})


@csrf_exempt
def replies(request, review_id):
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    review = Review.objects.filter(id=review_id).first()
    if not review:
        return _error(404, "REVIEW_NOT_FOUND", "Review not found.")
    data = _body(request)
    if not data.get("content"):
        return _error(400, "VALIDATION_ERROR", "Reply content is required.")
    try:
        staff_id = _uuid(request.headers.get("X-Staff-Id"), "staff_id")
    except ValueError:
        return _error(400, "VALIDATION_ERROR", "Staff id is required.")
    reply = CommentReply.objects.create(review=review, staff_id=staff_id, content=data["content"])
    return JsonResponse(_reply_payload(reply), status=201)


@csrf_exempt
def moderation(request, target_type, target_id):
    if request.method != "PATCH":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    data = _body(request)
    action = data.get("action")
    if action not in CommentModeration.Action.values:
        return _error(400, "VALIDATION_ERROR", "Invalid moderation action.")
    model = Review if target_type == "review" else CommentReply if target_type == "reply" else None
    if model is None:
        return _error(400, "VALIDATION_ERROR", "Invalid moderation target type.")
    target = model.objects.filter(id=target_id).first()
    if not target:
        return _error(404, "COMMENT_TARGET_NOT_FOUND", "Moderation target not found.")
    if action == CommentModeration.Action.HIDE:
        target.hide()
    else:
        target.show()
    moderated_by = _uuid(request.headers.get("X-Staff-Id"), "staff_id")
    CommentModeration.objects.create(
        target_type=target_type,
        target_id=target.id,
        action=action,
        moderated_by=moderated_by,
        reason=data.get("reason", ""),
    )
    return JsonResponse({"target_type": target_type, "target_id": str(target.id), "status": target.status})
