import json

from django.test import Client, TestCase


class ProductServiceApiTests(TestCase):
    def setUp(self):
        self.client = Client(HTTP_AUTHORIZATION="Bearer test-staff-token")

    def test_admin_creates_product_and_public_catalog_can_read_it(self):
        category = self.client.post(
            "/api/v1/products/admin/metadata/category",
            data=json.dumps({"name": "Fashion", "slug": "fashion", "status": "ACTIVE"}),
            content_type="application/json",
        )
        self.assertEqual(category.status_code, 201)

        brand = self.client.post(
            "/api/v1/products/admin/metadata/brand",
            data=json.dumps({"name": "Local Brand", "slug": "local-brand", "status": "ACTIVE"}),
            content_type="application/json",
        )
        self.assertEqual(brand.status_code, 201)

        tag = self.client.post(
            "/api/v1/products/admin/metadata/tag",
            data=json.dumps({"name": "basic", "slug": "basic", "status": "ACTIVE"}),
            content_type="application/json",
        )
        self.assertEqual(tag.status_code, 201)

        create_response = self.client.post(
            "/api/v1/products/admin/products",
            data=json.dumps(
                {
                    "name": "Basic T-Shirt",
                    "slug": "basic-t-shirt",
                    "sku": "TSHIRT-BASIC-001",
                    "category_id": category.json()["id"],
                    "brand_id": brand.json()["id"],
                    "price": 199000,
                    "original_price": 249000,
                    "stock_quantity": 120,
                    "status": "ACTIVE",
                    "tag_ids": [tag.json()["id"]],
                    "images": [
                        {
                            "url": "https://cdn.example.com/products/basic-t-shirt.jpg",
                            "is_thumbnail": True,
                        }
                    ],
                    "attributes": {"material": "Cotton", "color": "White"},
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(create_response.status_code, 201)
        product = create_response.json()
        self.assertEqual(product["sku"], "TSHIRT-BASIC-001")

        public_client = Client()
        list_response = public_client.get("/api/v1/products")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()["total"], 1)
        self.assertEqual(list_response.json()["items"][0]["thumbnail"], "https://cdn.example.com/products/basic-t-shirt.jpg")

        detail_response = public_client.get("/api/v1/products/basic-t-shirt")
        self.assertEqual(detail_response.status_code, 200)
        detail = detail_response.json()
        self.assertEqual(detail["brand"]["name"], "Local Brand")
        self.assertEqual(detail["tags"], ["basic"])
        self.assertEqual(detail["attributes"]["material"], "Cotton")

        search_response = public_client.get("/api/v1/products/search?q=shirt")
        self.assertEqual(search_response.status_code, 200)
        self.assertEqual(search_response.json()["total"], 1)

        stock_response = self.client.patch(
            f"/api/v1/products/admin/products/{product['id']}/stock",
            data=json.dumps({"stock_quantity": 150}),
            content_type="application/json",
        )
        self.assertEqual(stock_response.status_code, 200)
        self.assertEqual(stock_response.json()["stock_quantity"], 150)

        delete_response = self.client.delete(f"/api/v1/products/admin/products/{product['id']}")
        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(public_client.get("/api/v1/products").json()["total"], 0)

    def test_create_product_rejects_duplicate_sku(self):
        category = self.client.post(
            "/api/v1/products/admin/metadata/category",
            data=json.dumps({"name": "Fashion", "slug": "fashion"}),
            content_type="application/json",
        ).json()
        brand = self.client.post(
            "/api/v1/products/admin/metadata/brand",
            data=json.dumps({"name": "Local Brand", "slug": "local-brand"}),
            content_type="application/json",
        ).json()
        payload = {
            "name": "Basic T-Shirt",
            "slug": "basic-t-shirt",
            "sku": "TSHIRT-BASIC-001",
            "category_id": category["id"],
            "brand_id": brand["id"],
            "price": 199000,
            "stock_quantity": 120,
            "status": "ACTIVE",
        }

        first = self.client.post(
            "/api/v1/products/admin/products",
            data=json.dumps(payload),
            content_type="application/json",
        )
        second = self.client.post(
            "/api/v1/products/admin/products",
            data=json.dumps({**payload, "slug": "basic-t-shirt-2"}),
            content_type="application/json",
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json()["error"]["code"], "SKU_ALREADY_EXISTS")

    def test_patch_metadata_updates_existing_category(self):
        category = self.client.post(
            "/api/v1/products/admin/metadata/category",
            data=json.dumps({"name": "Fashion", "slug": "fashion"}),
            content_type="application/json",
        ).json()

        update_response = self.client.patch(
            "/api/v1/products/admin/metadata/category",
            data=json.dumps(
                {
                    "id": category["id"],
                    "name": "Fashion Updated",
                    "slug": "fashion-updated",
                    "status": "INACTIVE",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["name"], "Fashion Updated")
        self.assertEqual(update_response.json()["slug"], "fashion-updated")
        self.assertEqual(update_response.json()["status"], "INACTIVE")
