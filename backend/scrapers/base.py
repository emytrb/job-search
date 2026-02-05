from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, AsyncIterator
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from playwright_stealth import stealth_async
import hashlib
import logging
import os

from scrapers.rate_limiter import RateLimiter
from app.core.config import settings

logger = logging.getLogger(__name__)

# Get proxy URL from environment (set by docker-compose when VPN is enabled)
PROXY_URL = os.getenv("PROXY_URL")


@dataclass
class RawJob:
    external_id: str
    title: str
    company_name: str
    location: Optional[str]
    description: Optional[str]
    url: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    job_type: Optional[str] = None
    raw_data: Optional[dict] = None

    def compute_dedup_hash(self) -> str:
        content = f"{self.company_name.lower()}|{self.title.lower()}|{self.location or ''}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]


class BaseScraper(ABC):
    name: str = "base"

    def __init__(
        self,
        base_url: str,
        config: Optional[dict] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.config = config or {}
        self.rate_limiter = RateLimiter(
            min_delay=settings.scrape_rate_limit_min,
            max_delay=settings.scrape_rate_limit_max,
        )
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._playwright = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )

        # Configure proxy if available (routes traffic through VPN)
        context_options = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-GB",
        }

        if PROXY_URL:
            logger.info(f"Using proxy: {PROXY_URL}")
            context_options["proxy"] = {"server": PROXY_URL}

        self._context = await self._browser.new_context(**context_options)

    async def close(self) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def get_page(self) -> Page:
        if not self._context:
            raise RuntimeError("Scraper not started. Use 'async with' or call start()")
        page = await self._context.new_page()
        await stealth_async(page)
        return page

    async def fetch_with_rate_limit(self, page: Page, url: str) -> None:
        await self.rate_limiter.acquire()
        logger.info(f"Fetching: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

    @abstractmethod
    async def get_job_listings_url(self) -> str:
        pass

    @abstractmethod
    async def scrape_job_urls(self, page: Page) -> list[str]:
        pass

    @abstractmethod
    async def scrape_job_details(self, page: Page, url: str) -> Optional[RawJob]:
        pass

    async def scrape(self) -> AsyncIterator[RawJob]:
        page = await self.get_page()

        try:
            listings_url = await self.get_job_listings_url()
            await self.fetch_with_rate_limit(page, listings_url)

            job_urls = await self.scrape_job_urls(page)
            logger.info(f"Found {len(job_urls)} job URLs")

            for url in job_urls:
                try:
                    await self.fetch_with_rate_limit(page, url)
                    job = await self.scrape_job_details(page, url)
                    if job:
                        yield job
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    continue

        finally:
            await page.close()
