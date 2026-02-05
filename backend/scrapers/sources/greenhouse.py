from typing import Optional
from playwright.async_api import Page
import re
import logging

from scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)


class GreenhouseScraper(BaseScraper):
    name = "greenhouse"

    async def get_job_listings_url(self) -> str:
        return self.base_url

    async def scrape_job_urls(self, page: Page) -> list[str]:
        urls = []

        job_links = await page.query_selector_all('a[href*="/jobs/"]')

        for link in job_links:
            href = await link.get_attribute("href")
            if href:
                if href.startswith("/"):
                    href = f"https://boards.greenhouse.io{href}"
                elif not href.startswith("http"):
                    href = f"{self.base_url}/{href}"
                if "/jobs/" in href and href not in urls:
                    urls.append(href)

        return urls

    async def scrape_job_details(self, page: Page, url: str) -> Optional[RawJob]:
        try:
            title_el = await page.query_selector("h1.app-title, h1")
            title = await title_el.inner_text() if title_el else None

            if not title:
                return None

            company_el = await page.query_selector(".company-name, [class*='company']")
            company_name = await company_el.inner_text() if company_el else self._extract_company_from_url(url)

            location_el = await page.query_selector(".location, [class*='location']")
            location = await location_el.inner_text() if location_el else None

            content_el = await page.query_selector("#content, .content, main, article")
            description = await content_el.inner_text() if content_el else None

            external_id = self._extract_job_id(url)

            return RawJob(
                external_id=external_id,
                title=title.strip(),
                company_name=company_name.strip() if company_name else "Unknown",
                location=location.strip() if location else None,
                description=description,
                url=url,
            )

        except Exception as e:
            logger.error(f"Error parsing Greenhouse job {url}: {e}")
            return None

    def _extract_job_id(self, url: str) -> str:
        match = re.search(r"/jobs/(\d+)", url)
        if match:
            return f"gh_{match.group(1)}"
        return f"gh_{hash(url)}"

    def _extract_company_from_url(self, url: str) -> str:
        match = re.search(r"boards\.greenhouse\.io/(\w+)", url)
        if match:
            return match.group(1).replace("_", " ").title()

        match = re.search(r"greenhouse\.io/([^/]+)/jobs", url)
        if match:
            return match.group(1).replace("_", " ").title()

        return "Unknown"
