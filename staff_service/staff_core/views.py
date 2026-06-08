import json

from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Department, Permission, Role, StaffAccount, StaffRole


def _body(request):
    if not request.body:
        return {}
    return json.loads(request.body.decode("utf-8"))


def _error(status, code, message, details=None):
    return JsonResponse(
        {"error": {"code": code, "message": message, "details": details or {}}},
        status=status,
    )


def _require_auth(request):
    return request.headers.get("Authorization", "").startswith("Bearer ")


def _department_payload(department):
    return {"id": str(department.id), "code": department.code, "name": department.name, "status": department.status}


def _permission_payload(permission):
    return {
        "id": str(permission.id),
        "code": permission.code,
        "resource": permission.resource,
        "action": permission.action,
    }


def _role_payload(role):
    return {
        "id": str(role.id),
        "code": role.code,
        "name": role.name,
        "is_system_role": role.is_system_role,
        "permissions": list(role.permissions.order_by("code").values_list("code", flat=True)),
    }


def _staff_payload(staff):
    return {
        "id": str(staff.id),
        "employee_code": staff.employee_code,
        "email": staff.email,
        "full_name": staff.full_name,
        "phone": staff.phone,
        "department": {"id": str(staff.department_id), "name": staff.department.name},
        "status": staff.status,
        "roles": list(Role.objects.filter(staff_roles__staff=staff).order_by("code").values_list("code", flat=True)),
    }


@csrf_exempt
def departments(request):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    data = _body(request)
    if not data.get("code") or not data.get("name"):
        return _error(400, "VALIDATION_ERROR", "Code and name are required.")
    try:
        department = Department.objects.create(
            code=data["code"],
            name=data["name"],
            description=data.get("description", ""),
        )
    except IntegrityError:
        return _error(409, "DEPARTMENT_CODE_ALREADY_EXISTS", "Department code already exists.")
    return JsonResponse(_department_payload(department), status=201)


@csrf_exempt
def permissions(request):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    data = _body(request)
    required = ["code", "resource", "action"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return _error(400, "VALIDATION_ERROR", "Invalid permission.", {"missing": missing})
    try:
        permission = Permission.objects.create(
            code=data["code"],
            resource=data["resource"],
            action=data["action"],
            description=data.get("description", ""),
        )
    except IntegrityError:
        return _error(409, "PERMISSION_ALREADY_EXISTS", "Permission already exists.")
    return JsonResponse(_permission_payload(permission), status=201)


@csrf_exempt
def roles(request):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    if request.method == "GET":
        return JsonResponse({"items": [_role_payload(role) for role in Role.objects.order_by("code")]})
    if request.method == "POST":
        data = _body(request)
        if not data.get("code") or not data.get("name"):
            return _error(400, "VALIDATION_ERROR", "Code and name are required.")
        permission_ids = data.get("permission_ids", [])
        if Permission.objects.filter(id__in=permission_ids).count() != len(set(permission_ids)):
            return _error(404, "PERMISSION_NOT_FOUND", "Permission not found.")
        try:
            with transaction.atomic():
                role = Role.objects.create(
                    code=data["code"],
                    name=data["name"],
                    description=data.get("description", ""),
                    is_system_role=bool(data.get("is_system_role")),
                )
                role.set_permissions(permission_ids)
        except IntegrityError:
            return _error(409, "ROLE_ALREADY_EXISTS", "Role already exists.")
        return JsonResponse(_role_payload(role), status=201)
    return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")


@csrf_exempt
def role_permissions(request, role_id):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    if request.method != "PUT":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    role = Role.objects.filter(id=role_id).first()
    if not role:
        return _error(404, "ROLE_NOT_FOUND", "Role not found.")
    permission_ids = _body(request).get("permission_ids", [])
    if Permission.objects.filter(id__in=permission_ids).count() != len(set(permission_ids)):
        return _error(404, "PERMISSION_NOT_FOUND", "Permission not found.")
    role.set_permissions(permission_ids)
    return JsonResponse(_role_payload(role))


@csrf_exempt
def staff_members(request):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    if request.method == "GET":
        queryset = StaffAccount.objects.select_related("department").order_by("employee_code")
        department_id = request.GET.get("department_id")
        status = request.GET.get("status")
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if status:
            queryset = queryset.filter(status=status)
        items = [_staff_payload(staff) for staff in queryset]
        return JsonResponse({"items": items, "page": 1, "page_size": len(items) or 20, "total": len(items)})
    if request.method == "POST":
        data = _body(request)
        required = ["employee_code", "email", "full_name", "department_id"]
        missing = [field for field in required if not data.get(field)]
        if missing:
            return _error(400, "VALIDATION_ERROR", "Invalid staff member.", {"missing": missing})
        if StaffAccount.objects.filter(employee_code=data["employee_code"]).exists():
            return _error(409, "EMPLOYEE_CODE_ALREADY_EXISTS", "Employee code already exists.")
        if StaffAccount.objects.filter(email=data["email"]).exists():
            return _error(409, "EMAIL_ALREADY_EXISTS", "Email already exists.")
        department = Department.objects.filter(id=data["department_id"]).first()
        if not department:
            return _error(404, "DEPARTMENT_NOT_FOUND", "Department not found.")
        role_ids = data.get("role_ids", [])
        if Role.objects.filter(id__in=role_ids).count() != len(set(role_ids)):
            return _error(404, "ROLE_NOT_FOUND", "Role not found.")
        with transaction.atomic():
            staff = StaffAccount.objects.create(
                employee_code=data["employee_code"],
                email=data["email"],
                full_name=data["full_name"],
                phone=data.get("phone", ""),
                department=department,
                status=data.get("status", StaffAccount.Status.ACTIVE),
            )
            StaffRole.objects.bulk_create([StaffRole(staff=staff, role_id=role_id) for role_id in role_ids])
        return JsonResponse(_staff_payload(staff), status=201)
    return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")


@csrf_exempt
def staff_department(request, staff_id):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    if request.method != "PATCH":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    staff = StaffAccount.objects.filter(id=staff_id).first()
    if not staff:
        return _error(404, "STAFF_NOT_FOUND", "Staff not found.")
    department = Department.objects.filter(id=_body(request).get("department_id")).first()
    if not department:
        return _error(404, "DEPARTMENT_NOT_FOUND", "Department not found.")
    staff.department = department
    staff.save(update_fields=["department", "updated_at"])
    return JsonResponse(_staff_payload(staff))


@csrf_exempt
def staff_status(request, staff_id):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    if request.method != "PATCH":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    staff = StaffAccount.objects.filter(id=staff_id).first()
    if not staff:
        return _error(404, "STAFF_NOT_FOUND", "Staff not found.")
    status = _body(request).get("status")
    if status not in StaffAccount.Status.values:
        return _error(400, "VALIDATION_ERROR", "Invalid status.")
    staff.status = status
    staff.save(update_fields=["status", "updated_at"])
    return JsonResponse(_staff_payload(staff))


@csrf_exempt
def staff_roles(request, staff_id):
    if not _require_auth(request):
        return _error(401, "UNAUTHORIZED", "Unauthorized.")
    if request.method != "POST":
        return _error(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
    staff = StaffAccount.objects.filter(id=staff_id).first()
    if not staff:
        return _error(404, "STAFF_NOT_FOUND", "Staff not found.")
    role = Role.objects.filter(id=_body(request).get("role_id")).first()
    if not role:
        return _error(404, "ROLE_NOT_FOUND", "Role not found.")
    try:
        StaffRole.objects.create(staff=staff, role=role)
    except IntegrityError:
        return _error(409, "ROLE_ALREADY_ASSIGNED", "Role already assigned.")
    return JsonResponse(_staff_payload(staff), status=201)
