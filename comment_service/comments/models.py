import uuid

from django.db import models


class VisibleStatus(models.TextChoices):
    VISIBLE = "VISIBLE"
    HIDDEN = "HIDDEN"


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField()
    user_id = models.UUIDField()
    order_id = models.UUIDField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField()
    content = models.TextField()
    status = models.CharField(max_length=16, choices=VisibleStatus.choices, default=VisibleStatus.VISIBLE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def hide(self):
        self.status = VisibleStatus.HIDDEN
        self.save(update_fields=["status", "updated_at"])

    def show(self):
        self.status = VisibleStatus.VISIBLE
        self.save(update_fields=["status", "updated_at"])


class CommentReply(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="replies")
    staff_id = models.UUIDField()
    content = models.TextField()
    status = models.CharField(max_length=16, choices=VisibleStatus.choices, default=VisibleStatus.VISIBLE)
    created_at = models.DateTimeField(auto_now_add=True)

    def hide(self):
        self.status = VisibleStatus.HIDDEN
        self.save(update_fields=["status"])

    def show(self):
        self.status = VisibleStatus.VISIBLE
        self.save(update_fields=["status"])


class CommentModeration(models.Model):
    class Action(models.TextChoices):
        HIDE = "HIDE"
        SHOW = "SHOW"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    target_type = models.CharField(max_length=16)
    target_id = models.UUIDField()
    action = models.CharField(max_length=16, choices=Action.choices)
    moderated_by = models.UUIDField()
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
