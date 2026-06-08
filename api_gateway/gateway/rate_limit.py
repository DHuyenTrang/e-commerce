import time
from collections import defaultdict, deque

from django.conf import settings


_BUCKETS = defaultdict(deque)


def check_rate_limit(key):
    limit = getattr(settings, "GATEWAY_RATE_LIMIT_PER_MINUTE", 120)
    now = time.time()
    bucket = _BUCKETS[key]
    while bucket and now - bucket[0] >= 60:
        bucket.popleft()
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True
