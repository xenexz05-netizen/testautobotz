import time
from collections import defaultdict
from vars import Var


class RateLimiter:
    def __init__(self):
        self._user_requests: dict = defaultdict(list)
        self._global_requests: list = []

    def _clean_old(self, lst: list, window: float) -> list:
        now = time.time()
        return [t for t in lst if now - t < window]

    def is_rate_limited(self, user_id: int) -> bool:
        if not Var.RATE_LIMIT_ENABLED:
            return False
        window = Var.RATE_LIMIT_PERIOD_MINUTES * 60
        self._user_requests[user_id] = self._clean_old(self._user_requests[user_id], window)
        return len(self._user_requests[user_id]) >= Var.MAX_FILES_PER_PERIOD

    def record_request(self, user_id: int):
        self._user_requests[user_id].append(time.time())
        self._global_requests.append(time.time())

    def time_until_reset(self, user_id: int) -> int:
        if not self._user_requests[user_id]:
            return 0
        window = Var.RATE_LIMIT_PERIOD_MINUTES * 60
        oldest = min(self._user_requests[user_id])
        return max(0, int(window - (time.time() - oldest)))


rate_limiter = RateLimiter()
