import json
import uuid

from django.test import Client, TestCase


class ShippingServiceApiTests(TestCase):
    def setUp(self):
        self.client = Client(HTTP_AUTHORIZATION="Bearer staff-token")

    def test_carrier_fee_shipment_tracking_flow(self):
        carrier_response = self.client.post(
            "/api/v1/shipping/admin/carriers",
            data=json.dumps({"code": "GHN", "name": "GHN Express", "is_active": True}),
            content_type="application/json",
        )
        self.assertEqual(carrier_response.status_code, 201)

        rate_response = self.client.post(
            "/api/v1/shipping/admin/rates",
            data=json.dumps(
                {
                    "carrier_code": "GHN",
                    "province": "Ho Chi Minh",
                    "base_fee": 20000,
                    "fee_per_kg": 8000,
                    "estimated_days": 3,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(rate_response.status_code, 201)

        fee_response = self.client.post(
            "/api/v1/shipping/fees",
            data=json.dumps({"province": "Ho Chi Minh", "district": "District 1", "weight_kg": 1.5, "carrier_code": "GHN"}),
            content_type="application/json",
        )
        self.assertEqual(fee_response.status_code, 200)
        self.assertEqual(fee_response.json()["shipping_fee"], 32000)

        shipment_response = self.client.post(
            "/api/v1/shipping/admin/shipments",
            data=json.dumps(
                {
                    "order_id": str(uuid.uuid4()),
                    "carrier_code": "GHN",
                    "shipping_fee": 32000,
                    "receiver_address_snapshot": {"province": "Ho Chi Minh", "detail": "12 Nguyen Hue"},
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(shipment_response.status_code, 201)
        shipment = shipment_response.json()
        self.assertEqual(shipment["status"], "CREATED")

        tracking_response = self.client.patch(
            f"/api/v1/shipping/admin/shipments/{shipment['id']}/tracking",
            data=json.dumps({"status": "IN_TRANSIT", "location": "Hub", "description": "Picked up"}),
            content_type="application/json",
        )
        self.assertEqual(tracking_response.status_code, 200)
        self.assertEqual(tracking_response.json()["status"], "IN_TRANSIT")

        public_tracking = Client().get(f"/api/v1/shipping/track/{shipment['tracking_number']}")
        self.assertEqual(public_tracking.status_code, 200)
        self.assertEqual(public_tracking.json()["events"][0]["status"], "IN_TRANSIT")

    def test_shipping_fee_rejects_non_positive_weight(self):
        response = self.client.post(
            "/api/v1/shipping/fees",
            data=json.dumps({"province": "Ho Chi Minh", "weight_kg": 0, "carrier_code": "GHN"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")
