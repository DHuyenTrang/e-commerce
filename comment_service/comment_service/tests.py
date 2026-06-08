import json
import uuid

from django.test import Client, TestCase


class CommentServiceApiTests(TestCase):
    def setUp(self):
        self.customer = Client(
            HTTP_AUTHORIZATION="Bearer customer-token",
            HTTP_X_USER_ID=str(uuid.uuid4()),
        )
        self.staff = Client(
            HTTP_AUTHORIZATION="Bearer staff-token",
            HTTP_X_STAFF_ID=str(uuid.uuid4()),
        )

    def test_review_reply_and_moderation_flow(self):
        product_id = str(uuid.uuid4())
        review_response = self.customer.post(
            "/api/v1/comments/reviews",
            data=json.dumps(
                {
                    "product_id": product_id,
                    "order_id": str(uuid.uuid4()),
                    "rating": 5,
                    "content": "Good product.",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(review_response.status_code, 201)
        review = review_response.json()
        self.assertEqual(review["rating"], 5)

        reply_response = self.staff.post(
            f"/api/v1/comments/reviews/{review['id']}/replies",
            data=json.dumps({"content": "Thanks for your review."}),
            content_type="application/json",
        )
        self.assertEqual(reply_response.status_code, 201)

        list_response = Client().get(f"/api/v1/comments/products/{product_id}/reviews")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()["total"], 1)
        self.assertEqual(len(list_response.json()["items"][0]["replies"]), 1)

        moderation_response = self.staff.patch(
            f"/api/v1/comments/moderation/review/{review['id']}",
            data=json.dumps({"action": "HIDE", "reason": "Policy violation"}),
            content_type="application/json",
        )
        self.assertEqual(moderation_response.status_code, 200)
        self.assertEqual(moderation_response.json()["status"], "HIDDEN")
        self.assertEqual(Client().get(f"/api/v1/comments/products/{product_id}/reviews").json()["total"], 0)

    def test_submit_review_rejects_rating_outside_one_to_five(self):
        response = self.customer.post(
            "/api/v1/comments/reviews",
            data=json.dumps(
                {
                    "product_id": str(uuid.uuid4()),
                    "rating": 6,
                    "content": "Invalid rating.",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")
