from dataclasses import dataclass


@dataclass
class Identity:
    subject_type: str
    subject_id: str
    roles: list[str]
    permissions: list[str]


def parse_bearer_token(authorization_header):
    if not authorization_header or not authorization_header.startswith("Bearer "):
        return None
    token = authorization_header.removeprefix("Bearer ").strip()
    if not token:
        return None

    head, *parts = token.split(";")
    if ":" not in head:
        return None
    subject_type, subject_id = head.split(":", 1)
    if subject_type not in {"user", "staff"} or not subject_id:
        return None

    claims = {"roles": [], "permissions": []}
    for part in parts:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        if key in claims:
            claims[key] = [item for item in value.split(",") if item]

    return Identity(
        subject_type=subject_type,
        subject_id=subject_id,
        roles=claims["roles"],
        permissions=claims["permissions"],
    )
