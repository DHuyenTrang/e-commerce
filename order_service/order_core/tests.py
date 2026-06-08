import json
import uuid

from django.test import TestCase


class OrderServiceApiTests(TestCase):
    def setUp(self):
        self.user_id = str(uuid.uuid4())
        self.other_user_id = str(uuid.uuid4())
        self.staff_id = str(uuid.uuid4())
        self.item = {
            "product_id": str(uuid.uuid4()),
            "sku": "TEE-BASIC",
            "product_name": "Basic Tee",
            "unit_price": 199000,
            "quantity": 2,
        }
        self.address = {
            "receiver_name": "Nguyen Van A",
            "phone": "0900000000",
            "province": "Ho Chi Minh",
            "line1": "1 Nguyen Hue",
        }

    def _post_json(self, path, payload, **headers):
        return self.client.post(path, data=json.dumps(payload), content_type="application/json", **headers)

    def _patch_json(self, path, payload, **headers):
        return self.client.patch(path, data=json.dumps(payload), content_type="application/json", **headers)

    def _initiate_checkout(self, user_id=None):
        return self._post_json(
            "/api/v1/orders/checkout/initiate",
            {
                "cart_id": str(uuid.uuid4()),
                "shipping_address_id": str(uuid.uuid4()),
                "shipping_address_snapshot": self.address,
                "shipping_fee": 30000,
                "items": [self.item],
            },
            HTTP_X_USER_ID=user_id or self.user_id,
        )

    def _place_order(self, checkout_id, user_id=None):
        return self._post_json(
            "/api/v1/orders/checkout/place-order",
            {"checkout_id": checkout_id, "payment_method": "COD"},
            HTTP_X_USER_ID=user_id or self.user_id,
        )

    def test_initiate_checkout_creates_checkout_session_summary(self):
        response = self._initiate_checkout()

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertIn("checkout_id", payload)
        self.assertEqual(payload["subtotal"], 398000)
        self.assertEqual(payload["shipping_fee"], 30000)
        self.assertEqual(payload["total_amount"], 428000)
        self.assertIn("expires_at", payload)

    def test_place_order_creates_order_from_checkout_snapshot(self):
        checkout = self._initiate_checkout().json()

        response = self._place_order(checkout["checkout_id"])

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertIn("id", payload)
        self.assertTrue(payload["order_code"].startswith("ORD-"))
        self.assertEqual(payload["status"], "CONFIRMED")
        self.assertEqual(payload["total_amount"], 428000)

    def test_customer_can_only_list_their_own_orders(self):
        checkout = self._initiate_checkout().json()
        order = self._place_order(checkout["checkout_id"]).json()

        response = self.client.get("/api/v1/orders/me", HTTP_X_USER_ID=self.other_user_id)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total"], 0)
        self.assertNotIn(order["id"], [item["id"] for item in payload["items"]])

    def test_get_order_detail_includes_items_for_owner(self):
        checkout = self._initiate_checkout().json()
        order = self._place_order(checkout["checkout_id"]).json()

        response = self.client.get(f"/api/v1/orders/me/{order['id']}", HTTP_X_USER_ID=self.user_id)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["id"], order["id"])
        self.assertEqual(payload["items"][0]["sku"], "TEE-BASIC")
        self.assertEqual(payload["items"][0]["line_total"], 398000)

    def test_cancel_order_request_records_cancel_requested_status(self):
        checkout = self._initiate_checkout().json()
        order = self._place_order(checkout["checkout_id"]).json()

        response = self._post_json(
            f"/api/v1/orders/me/{order['id']}/cancel-request",
            {"reason": "Change shipping address"},
            HTTP_X_USER_ID=self.user_id,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "CANCEL_REQUESTED")
        self.assertEqual(payload["latest_status_history"]["new_status"], "CANCEL_REQUESTED")

    def test_admin_rejects_invalid_status_transition(self):
        checkout = self._initiate_checkout().json()
        order = self._place_order(checkout["checkout_id"]).json()

        response = self._patch_json(
            f"/api/v1/orders/admin/orders/{order['id']}/status",
            {"status": "PENDING_PAYMENT", "note": "Invalid rollback"},
            HTTP_X_STAFF_ID=self.staff_id,
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "INVALID_ORDER_STATUS_TRANSITION")
