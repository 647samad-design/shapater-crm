"""Brute-force protection for login. In-memory (per process): fine for one instance.
For several API instances move this to Redis (same interface)."""
import time
from collections import defaultdict, deque

from app.core.config import settings


class LoginLimiter:
    def __init__(self) -> None:
        self._fails: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, key: str) -> deque[float]:
        q = self._fails[key]
        cutoff = time.monotonic() - settings.login_window_seconds
        while q and q[0] < cutoff:
            q.popleft()
        return q

    def retry_after(self, key: str) -> int:
        """Seconds until the next attempt is allowed (0 = allowed)."""
        q = self._prune(key)
        if len(q) < settings.login_max_failures:
            return 0
        return max(1, int(q[0] + settings.login_window_seconds - time.monotonic()))

    def fail(self, key: str) -> None:
        self._prune(key).append(time.monotonic())

    def reset(self, key: str) -> None:
        self._fails.pop(key, None)

    def clear(self) -> None:
        self._fails.clear()


login_limiter = LoginLimiter()
