from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings


def forward_request(*, service_name, method, path, query_string, headers, body):
    service_urls = getattr(settings, "GATEWAY_SERVICE_URLS", {})
    base_url = service_urls.get(service_name)
    if not base_url:
        raise URLError(f"Service URL is not configured for {service_name}.")
    url = f"{base_url.rstrip('/')}{path}"
    if query_string:
        url = f"{url}?{query_string}"
    request = Request(url, data=body or None, method=method, headers=headers)
    try:
        with urlopen(request, timeout=getattr(settings, "GATEWAY_TIMEOUT_SECONDS", 5)) as response:
            return {
                "status_code": response.status,
                "content": response.read(),
                "headers": dict(response.headers.items()),
            }
    except HTTPError as error:
        return {
            "status_code": error.code,
            "content": error.read(),
            "headers": dict(error.headers.items()),
        }
