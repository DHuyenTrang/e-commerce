import json
import uuid

from django.test import Client, TestCase


class PaymentServiceApiTests(TestCase):
    def setUp(self):
        self.client = Client(HTTP_AUTHORIZATION="Bearer order-token")

    def test_method_transaction_callback_and_status_flow(self):
        method_response = self.client.post(
            "/api/v1/payments/admin/methods",
            data=json.dumps({"code": "VNPAY", "name": "VNPay", "provider": "VNPAY", "is_active": True}),
            content_type="application/json",
        )
        self.assertEqual(method_response.status_code, 201)

        methods_response = Client().get("/api/v1/payments/methods")
        self.assertEqual(methods_response.status_code, 200)
        self.assertEqual(methods_response.json()["items"][0]["code"], "VNPAY")

        transaction_response = self.client.post(
            "/api/v1/payments/transactions",
            data=json.dumps(
                {
                    "order_id": str(uuid.uuid4()),
                    "amount": 428000,
                    "currency": "VND",
                    "payment_method_code": "VNPAY",
                    "return_url": "https://shop.example.com/payment-result",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(transaction_response.status_code, 201)
        transaction = transaction_response.json()
        self.assertEqual(transaction["status"], "PENDING")

        callback_response = Client().post(
            "/api/v1/payments/callbacks/vnpay",
            data=json.dumps(
                {
                    "transaction_code": transaction["transaction_code"],
                    "status": "SUCCESS",
                    "gateway_reference": "VNPAY-123456",
                    "signature_valid": True,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(callback_response.status_code, 200)
        self.assertEqual(callback_response.json()["status"], "SUCCESS")

        status_response = self.client.get(f"/api/v1/payments/transactions/{transaction['id']}/status")
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()["status"], "SUCCESS")

    def test_create_transaction_rejects_non_positive_amount(self):
        response = self.client.post(
            "/api/v1/payments/transactions",
            data=json.dumps(
                {
                    "order_id": str(uuid.uuid4()),
                    "amount": 0,
                    "currency": "VND",
                    "payment_method_code": "COD",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")
