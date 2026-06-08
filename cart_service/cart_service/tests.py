import json
import uuid

from django.test import Client, TestCase


class CartServiceApiTests(TestCase):
    def setUp(self):
        self.client = Client(HTTP_X_GUEST_SESSION_ID="guest-session-1")

    def test_cart_item_lifecycle_for_guest_session(self):
        empty_response = self.client.get("/api/v1/cart")
        self.assertEqual(empty_response.status_code, 200)
        self.assertEqual(empty_response.json()["items"], [])

        product_id = str(uuid.uuid4())
        add_response = self.client.post(
            "/api/v1/cart/items",
            data=json.dumps(
                {
                    "product_id": product_id,
                    "sku": "TSHIRT-BASIC-001",
                    "quantity": 1,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(add_response.status_code, 201)
        item = add_response.json()
        self.assertEqual(item["quantity"], 1)

        merge_response = self.client.post(
            "/api/v1/cart/items",
            data=json.dumps(
                {
                    "product_id": product_id,
                    "sku": "TSHIRT-BASIC-001",
                    "quantity": 2,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(merge_response.status_code, 201)
        self.assertEqual(merge_response.json()["quantity"], 3)

        update_response = self.client.patch(
            f"/api/v1/cart/items/{item['id']}",
            data=json.dumps({"quantity": 5}),
            content_type="application/json",
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["quantity"], 5)

        cart_response = self.client.get("/api/v1/cart")
        self.assertEqual(cart_response.status_code, 200)
        self.assertEqual(cart_response.json()["items"][0]["quantity"], 5)

        delete_response = self.client.delete(f"/api/v1/cart/items/{item['id']}")
        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(self.client.get("/api/v1/cart").json()["items"], [])

    def test_add_item_rejects_invalid_quantity(self):
        response = self.client.post(
            "/api/v1/cart/items",
            data=json.dumps(
                {
                    "product_id": str(uuid.uuid4()),
                    "sku": "TSHIRT-BASIC-001",
                    "quantity": 0,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "INVALID_QUANTITY")
