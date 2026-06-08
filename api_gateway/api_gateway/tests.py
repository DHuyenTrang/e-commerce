import json
from unittest.mock import patch

from django.test import Client, TestCase, override_settings


def upstream_response(status=200, payload=None, headers=None):
    return {
        "status_code": status,
        "content": json.dumps(payload or {"ok": True}).encode("utf-8"),
        "headers": {"Content-Type": "application/json", **(headers or {})},
    }


@override_settings(
    GATEWAY_RATE_LIMIT_PER_MINUTE=2,
    GATEWAY_JWT_SECRET="test-secret",
    GATEWAY_SERVICE_URLS={
        "products": "http://product-service.test",
        "cart": "http://cart-service.test",
        "staff": "http://staff-service.test",
    },
)
class ApiGatewayTests(TestCase):
    def setUp(self):
        self.client = Client()

    @patch("gateway.proxy.forward_request")
    def test_public_product_route_forwards_without_token_and_request_id(self, forward_request):
        forward_request.return_value = upstream_response(payload={"items": []})

        response = self.client.get("/api/v1/products?category=fashion", HTTP_X_REQUEST_ID="req-test-1")

        self.assertEqual(response.status_code, 200)
        target = forward_request.call_args.kwargs
        self.assertEqual(target["service_name"], "products")
        self.assertEqual(target["path"], "/api/v1/products")
        self.assertEqual(target["query_string"], "category=fashion")
        self.assertEqual(target["headers"]["X-Request-Id"], "req-test-1")

    def test_private_cart_route_requires_bearer_token(self):
        response = self.client.get("/api/v1/cart")

        self.assertEqual(response.status_code, 401)
        body = response.json()
        self.assertEqual(body["error"]["code"], "UNAUTHORIZED")
        self.assertIn("request_id", body["error"])

    @patch("gateway.proxy.forward_request")
    def test_customer_token_forwards_identity_headers_to_private_route(self, forward_request):
        forward_request.return_value = upstream_response(payload={"items": []})

        response = self.client.get(
            "/api/v1/cart",
            HTTP_AUTHORIZATION="Bearer user:user-123",
            HTTP_X_REQUEST_ID="req-cart-1",
        )

        self.assertEqual(response.status_code, 200)
        headers = forward_request.call_args.kwargs["headers"]
        self.assertEqual(headers["X-User-Id"], "user-123")
        self.assertEqual(headers["X-Request-Id"], "req-cart-1")

    def test_admin_route_requires_permission(self):
        response = self.client.post(
            "/api/v1/products/admin/products",
            data=json.dumps({"name": "Test"}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer staff:staff-1;permissions=product:read",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")

    @patch("gateway.proxy.forward_request")
    def test_admin_route_forwards_staff_context_when_permission_exists(self, forward_request):
        forward_request.return_value = upstream_response(status=201, payload={"id": "product-1"})

        response = self.client.post(
            "/api/v1/products/admin/products",
            data=json.dumps({"name": "Test"}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer staff:staff-1;roles=ADMIN;permissions=product:create,product:update",
        )

        self.assertEqual(response.status_code, 201)
        headers = forward_request.call_args.kwargs["headers"]
        self.assertEqual(headers["X-Staff-Id"], "staff-1")
        self.assertEqual(headers["X-Roles"], "ADMIN")
        self.assertEqual(headers["X-Permissions"], "product:create,product:update")

    @patch("gateway.proxy.forward_request")
    def test_rate_limit_returns_429_after_limit_is_exceeded(self, forward_request):
        forward_request.return_value = upstream_response()

        self.client.get("/api/v1/products", REMOTE_ADDR="10.0.0.1")
        self.client.get("/api/v1/products", REMOTE_ADDR="10.0.0.1")
        response = self.client.get("/api/v1/products", REMOTE_ADDR="10.0.0.1")

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["error"]["code"], "RATE_LIMIT_EXCEEDED")

    def test_unknown_route_returns_standard_404(self):
        response = self.client.get("/api/v1/unknown")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "ROUTE_NOT_FOUND")
