from typing import Optional
from playwright.async_api import Page
import re
import logging

from scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)


class LeverScraper(BaseScraper):
    name = "lever"

    async def get_job_listings_url(self) -> str:
        return self.base_url

    async def scrape_job_urls(self, page: Page) -> list[str]:
        urls = []

        job_links = await page.query_selector_all('a.posting-title, a[href*="/jobs/"]')

        for link in job_links:
            href = await link.get_attribute("href")
            if href and href not in urls:
                if not href.startswith("http"):
                    href = f"https://jobs.lever.co{href}"
                urls.append(href)

        return urls

    async def scrape_job_details(self, page: Page, url: str) -> Optional[RawJob]:
        try:
            title_el = await page.query_selector("h2.posting-headline, h1")
            title = await title_el.inner_text() if title_el else None

            if not title:
                return None

            company_name = self._extract_company_from_url(url)

            location_el = await page.query_selector(".location, .posting-categories .sort-by-location")
            location = await location_el.inner_text() if location_el else None

            content_el = await page.query_selector(".content, .posting-page, main")
            description = await content_el.inner_text() if content_el else None

            external_id = self._extract_job_id(url)

            return RawJob(
                external_id=external_id,
                title=title.strip(),
                company_name=company_name,
                location=location.strip() if location else None,
                description=description,
                url=url,
            )

        except Exception as e:
            logger.error(f"Error parsing Lever job {url}: {e}")
            return None

    def _extract_job_id(self, url: str) -> str:
        match = re.search(r"/([a-f0-9-]{36})", url)
        if match:
            return f"lever_{match.group(1)}"
        return f"lever_{hash(url)}"

    def _extract_company_from_url(self, url: str) -> str:
        match = re.search(r"jobs\.lever\.co/([^/]+)", url)
        if match:
            return match.group(1).replace("-", " ").title()
        return "Unknown"
