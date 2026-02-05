import asyncio
import random
import time
from typing import Optional


class RateLimiter:
    def __init__(
        self,
        min_delay: float = 5.0,
        max_delay: float = 15.0,
        burst_limit: int = 10,
        burst_window: float = 60.0,
    ):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.burst_limit = burst_limit
        self.burst_window = burst_window
        self.request_times: list[float] = []
        self._lock = asyncio.Lock()

    def _get_jitter_delay(self) -> float:
        return random.uniform(self.min_delay, self.max_delay)

    def _clean_old_requests(self) -> None:
        now = time.time()
        cutoff = now - self.burst_window
        self.request_times = [t for t in self.request_times if t > cutoff]

    async def acquire(self) -> None:
        async with self._lock:
            self._clean_old_requests()

            if len(self.request_times) >= self.burst_limit:
                oldest = self.request_times[0]
                wait_time = self.burst_window - (time.time() - oldest)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    self._clean_old_requests()

            delay = self._get_jitter_delay()
            await asyncio.sleep(delay)

            self.request_times.append(time.time())

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class DomainRateLimiter:
    def __init__(
        self,
        min_delay: float = 5.0,
        max_delay: float = 15.0,
    ):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self._limiters: dict[str, RateLimiter] = {}
        self._lock = asyncio.Lock()

    async def get_limiter(self, domain: str) -> RateLimiter:
        async with self._lock:
            if domain not in self._limiters:
                self._limiters[domain] = RateLimiter(
                    min_delay=self.min_delay,
                    max_delay=self.max_delay,
                )
            return self._limiters[domain]

    async def acquire(self, domain: str) -> None:
        limiter = await self.get_limiter(domain)
        await limiter.acquire()
