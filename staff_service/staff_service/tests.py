import json

from django.test import Client, TestCase


class StaffServiceApiTests(TestCase):
    def setUp(self):
        self.client = Client(HTTP_AUTHORIZATION="Bearer test-admin-token")

    def test_create_list_update_staff_and_assign_role(self):
        department_response = self.client.post(
            "/api/v1/staff/departments",
            data=json.dumps({"code": "OPS", "name": "Operations"}),
            content_type="application/json",
        )
        self.assertEqual(department_response.status_code, 201)
        department_id = department_response.json()["id"]

        permission_response = self.client.post(
            "/api/v1/staff/permissions",
            data=json.dumps(
                {
                    "code": "staff:read",
                    "resource": "staff",
                    "action": "read",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(permission_response.status_code, 201)
        permission_id = permission_response.json()["id"]

        role_response = self.client.post(
            "/api/v1/staff/roles",
            data=json.dumps(
                {
                    "code": "STAFF",
                    "name": "Staff",
                    "permission_ids": [permission_id],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(role_response.status_code, 201)
        role_id = role_response.json()["id"]

        create_response = self.client.post(
            "/api/v1/staff/members",
            data=json.dumps(
                {
                    "employee_code": "EMP001",
                    "email": "staff@example.com",
                    "full_name": "Tran Thi B",
                    "phone": "0909333444",
                    "department_id": department_id,
                    "role_ids": [role_id],
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(create_response.status_code, 201)
        staff = create_response.json()
        self.assertEqual(staff["employee_code"], "EMP001")

        list_response = self.client.get("/api/v1/staff/members")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()["total"], 1)
        self.assertEqual(list_response.json()["items"][0]["roles"], ["STAFF"])

        status_response = self.client.patch(
            f"/api/v1/staff/members/{staff['id']}/status",
            data=json.dumps({"status": "LOCKED", "reason": "Offboarded"}),
            content_type="application/json",
        )
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()["status"], "LOCKED")

        roles_response = self.client.get("/api/v1/staff/roles")
        self.assertEqual(roles_response.status_code, 200)
        self.assertEqual(roles_response.json()["items"][0]["permissions"], ["staff:read"])

    def test_create_staff_rejects_duplicate_employee_code(self):
        department_response = self.client.post(
            "/api/v1/staff/departments",
            data=json.dumps({"code": "OPS", "name": "Operations"}),
            content_type="application/json",
        )
        department_id = department_response.json()["id"]
        payload = {
            "employee_code": "EMP001",
            "email": "staff@example.com",
            "full_name": "Tran Thi B",
            "department_id": department_id,
        }

        first = self.client.post(
            "/api/v1/staff/members",
            data=json.dumps(payload),
            content_type="application/json",
        )
        second = self.client.post(
            "/api/v1/staff/members",
            data=json.dumps({**payload, "email": "other.staff@example.com"}),
            content_type="application/json",
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json()["error"]["code"], "EMPLOYEE_CODE_ALREADY_EXISTS")
