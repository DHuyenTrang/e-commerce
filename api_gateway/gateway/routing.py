from dataclasses import dataclass


@dataclass(frozen=True)
class Route:
    prefix: str
    service_name: str
    public_prefixes: tuple[str, ...] = ()
    admin_permissions: tuple[tuple, ...] = ()
    private: bool = True

    def is_public(self, path):
        return any(path.startswith(prefix) for prefix in self.public_prefixes)

    def required_permission(self, path, method):
        for rule in self.admin_permissions:
            prefix, permission = rule[:2]
            methods = rule[2] if len(rule) > 2 else None
            if methods and method not in methods:
                continue
            if path.startswith(prefix):
                return permission
        return None


ROUTES = (
    Route(
        prefix="/api/v1/users",
        service_name="users",
        public_prefixes=("/api/v1/users/auth/register", "/api/v1/users/auth/login"),
    ),
    Route(prefix="/api/v1/staff", service_name="staff", private=True),
    Route(
        prefix="/api/v1/products",
        service_name="products",
        private=False,
        public_prefixes=("/api/v1/products",),
        admin_permissions=(
            ("/api/v1/products/admin/products", "product:create"),
            ("/api/v1/products/admin/metadata", "product:manage_metadata"),
        ),
    ),
    Route(prefix="/api/v1/cart", service_name="cart", private=True),
    Route(
        prefix="/api/v1/orders",
        service_name="orders",
        private=True,
        admin_permissions=(
            ("/api/v1/orders/admin/orders", "order:read_all", ("GET",)),
            ("/api/v1/orders/admin/orders", "order:update_status", ("PATCH",)),
        ),
    ),
    Route(prefix="/api/v1/payments", service_name="payments", public_prefixes=("/api/v1/payments/methods", "/api/v1/payments/callbacks")),
    Route(prefix="/api/v1/shipping", service_name="shipping", public_prefixes=("/api/v1/shipping/track",)),
    Route(prefix="/api/v1/ai", service_name="ai", private=True),
    Route(prefix="/api/v1/comments", service_name="comments", public_prefixes=("/api/v1/comments/products",)),
)


def resolve_route(path):
    matches = [route for route in ROUTES if path == route.prefix or path.startswith(route.prefix + "/")]
    if not matches:
        return None
    return max(matches, key=lambda route: len(route.prefix))
