import json

from django.test import Client, TestCase


class UserServiceApiTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_login_profile_and_address_flow(self):
        register_response = self.client.post(
            "/api/v1/users/auth/register",
            data=json.dumps(
                {
                    "email": "customer@example.com",
                    "phone": "0909123456",
                    "password": "StrongPassword@123",
                    "full_name": "Nguyen Van A",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(register_response.status_code, 201)
        registered = register_response.json()
        self.assertEqual(registered["email"], "customer@example.com")
        self.assertNotIn("password_hash", registered)
        self.assertEqual(registered["profile"]["full_name"], "Nguyen Van A")

        login_response = self.client.post(
            "/api/v1/users/auth/login",
            data=json.dumps(
                {
                    "identifier": "customer@example.com",
                    "password": "StrongPassword@123",
                    "device_info": "Django test client",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(login_response.status_code, 200)
        token_payload = login_response.json()
        self.assertEqual(token_payload["token_type"], "Bearer")
        self.assertIn("access_token", token_payload)
        self.assertIn("refresh_token", token_payload)

        auth = f"Bearer {token_payload['access_token']}"
        address_response = self.client.post(
            "/api/v1/users/me/addresses",
            data=json.dumps(
                {
                    "recipient_name": "Nguyen Van A",
                    "recipient_phone": "0909123456",
                    "province": "Ho Chi Minh",
                    "district": "District 1",
                    "ward": "Ben Nghe",
                    "detail": "12 Nguyen Hue",
                    "is_default": True,
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION=auth,
        )

        self.assertEqual(address_response.status_code, 201)
        address = address_response.json()
        self.assertTrue(address["is_default"])

        profile_response = self.client.get(
            "/api/v1/users/me",
            HTTP_AUTHORIZATION=auth,
        )

        self.assertEqual(profile_response.status_code, 200)
        profile = profile_response.json()
        self.assertEqual(profile["email"], "customer@example.com")
        self.assertEqual(len(profile["addresses"]), 1)

        delete_response = self.client.delete(
            f"/api/v1/users/me/addresses/{address['id']}",
            HTTP_AUTHORIZATION=auth,
        )

        self.assertEqual(delete_response.status_code, 204)

    def test_register_rejects_duplicate_email(self):
        payload = {
            "email": "customer@example.com",
            "phone": "0909123456",
            "password": "StrongPassword@123",
            "full_name": "Nguyen Van A",
        }
        first = self.client.post(
            "/api/v1/users/auth/register",
            data=json.dumps(payload),
            content_type="application/json",
        )
        second_payload = {
            **payload,
            "phone": "0909000000",
        }
        second = self.client.post(
            "/api/v1/users/auth/register",
            data=json.dumps(second_payload),
            content_type="application/json",
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json()["error"]["code"], "EMAIL_ALREADY_EXISTS")
