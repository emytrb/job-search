from typing import Optional
from playwright.async_api import Page
import re
import logging

from scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)


class WTTJScraper(BaseScraper):
    name = "wttj"

    async def get_job_listings_url(self) -> str:
        return self.base_url

    async def scrape_job_urls(self, page: Page) -> list[str]:
        urls = []

        await page.wait_for_selector('a[href*="/jobs/"]', timeout=10000)
        job_links = await page.query_selector_all('a[href*="/jobs/"]')

        for link in job_links:
            href = await link.get_attribute("href")
            if href and "/jobs/" in href and href not in urls:
                if not href.startswith("http"):
                    href = f"https://www.welcometothejungle.com{href}"
                urls.append(href)

        return urls

    async def scrape_job_details(self, page: Page, url: str) -> Optional[RawJob]:
        try:
            await page.wait_for_selector("h1, h2", timeout=10000)

            title_el = await page.query_selector("h1")
            title = await title_el.inner_text() if title_el else None

            if not title:
                return None

            company_el = await page.query_selector('[data-testid="job-company-name"], a[href*="/companies/"]')
            company_name = await company_el.inner_text() if company_el else self._extract_company_from_url(url)

            location_el = await page.query_selector('[data-testid="job-location"], [class*="location"]')
            location = await location_el.inner_text() if location_el else None

            content_el = await page.query_selector('[data-testid="job-section-description"], .job-description, main')
            description = await content_el.inner_text() if content_el else None

            salary_text = await self._extract_salary(page)
            salary_min, salary_max, currency = self._parse_salary(salary_text)

            external_id = self._extract_job_id(url)

            return RawJob(
                external_id=external_id,
                title=title.strip(),
                company_name=company_name.strip() if company_name else "Unknown",
                location=location.strip() if location else None,
                description=description,
                url=url,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=currency,
            )

        except Exception as e:
            logger.error(f"Error parsing WTTJ job {url}: {e}")
            return None

    async def _extract_salary(self, page: Page) -> Optional[str]:
        salary_el = await page.query_selector('[data-testid="job-salary"], [class*="salary"]')
        if salary_el:
            return await salary_el.inner_text()
        return None

    def _parse_salary(self, salary_text: Optional[str]) -> tuple[Optional[int], Optional[int], Optional[str]]:
        if not salary_text:
            return None, None, None

        currency = "GBP" if "£" in salary_text else "EUR" if "€" in salary_text else "USD"

        numbers = re.findall(r"[\d,]+", salary_text.replace(",", ""))
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1]), currency
        elif len(numbers) == 1:
            return int(numbers[0]), None, currency

        return None, None, None

    def _extract_job_id(self, url: str) -> str:
        match = re.search(r"/jobs/([^/?]+)", url)
        if match:
            return f"wttj_{match.group(1)}"
        return f"wttj_{hash(url)}"

    def _extract_company_from_url(self, url: str) -> str:
        match = re.search(r"/companies/([^/]+)", url)
        if match:
            return match.group(1).replace("-", " ").title()
        return "Unknown"
