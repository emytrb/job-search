from typing import Optional
from playwright.async_api import Page
import re
import logging
import asyncio

from scrapers.base import BaseScraper, RawJob
from app.core.config import settings

logger = logging.getLogger(__name__)


class IndeedScraper(BaseScraper):
    name = "indeed"

    def __init__(self, base_url: str, config: Optional[dict] = None):
        super().__init__(base_url, config)
        self.rate_limiter.min_delay = 10.0
        self.rate_limiter.max_delay = 20.0

    async def get_job_listings_url(self) -> str:
        return self.base_url

    async def scrape_job_urls(self, page: Page) -> list[str]:
        urls = []

        # Wait for page to load - Indeed's challenge pages sometimes resolve after a delay
        await asyncio.sleep(5)

        # Debug: log page title and check for common block indicators
        title = await page.title()
        logger.info(f"Indeed page title: {title}")

        # If we hit a challenge page, wait longer for it to potentially resolve
        if "moment" in title.lower() or "verify" in title.lower():
            logger.info("Challenge page detected, waiting for it to resolve...")
            await asyncio.sleep(10)
            # Simulate some human-like behavior
            await page.mouse.move(100, 200)
            await asyncio.sleep(1)
            await page.mouse.move(300, 400)
            await asyncio.sleep(5)
            title = await page.title()
            logger.info(f"Indeed page title after wait: {title}")

        # Check if we hit a CAPTCHA or block page
        captcha = await page.query_selector('iframe[src*="captcha"], #captcha, .captcha')
        if captcha:
            logger.warning("Indeed CAPTCHA detected - scraping blocked")
            return []

        # Check for the job results container first
        results_container = await page.query_selector('#mosaic-jobResults, .jobsearch-ResultsList')
        if not results_container:
            logger.warning("Indeed job results container not found - page may not have loaded correctly")
            # Save page content for debugging
            content = await page.content()
            logger.warning(f"Page content length: {len(content)} chars")
            # Save to file for inspection
            try:
                with open("/app/debug_indeed_page.html", "w") as f:
                    f.write(content)
                logger.warning("Saved page to /app/debug_indeed_page.html for inspection")
            except Exception as e:
                logger.error(f"Failed to save debug page: {e}")
            return []

        # Try multiple selectors for job cards
        job_cards = await page.query_selector_all('a.jcs-JobTitle[data-jk]')
        logger.info(f"Found {len(job_cards)} job cards with selector 'a.jcs-JobTitle[data-jk]'")

        if not job_cards:
            # Fallback selectors
            job_cards = await page.query_selector_all('a[data-jk]')
            logger.info(f"Fallback: found {len(job_cards)} elements with 'a[data-jk]'")

        if not job_cards:
            job_cards = await page.query_selector_all('.cardOutline.tapItem a[href*="/rc/clk"]')
            logger.info(f"Fallback 2: found {len(job_cards)} elements with '.cardOutline.tapItem a[href*=\"/rc/clk\"]'")

        for card in job_cards:
            href = await card.get_attribute("href")
            if href:
                if not href.startswith("http"):
                    href = f"https://uk.indeed.com{href}"
                if href not in urls:
                    urls.append(href)

        logger.info(f"Indeed: extracted {len(urls)} unique job URLs")
        return urls[:20]

    async def scrape_job_details(self, page: Page, url: str) -> Optional[RawJob]:
        try:
            await asyncio.sleep(1)

            title_el = await page.query_selector('h1.jobsearch-JobInfoHeader-title, h1[data-testid="jobsearch-JobInfoHeader-title"]')
            title = await title_el.inner_text() if title_el else None

            if not title:
                return None

            company_el = await page.query_selector('[data-testid="inlineHeader-companyName"] a, .jobsearch-InlineCompanyRating-companyHeader a')
            company_name = await company_el.inner_text() if company_el else "Unknown"

            location_el = await page.query_selector('[data-testid="job-location"], .jobsearch-JobInfoHeader-subtitle > div:nth-child(2)')
            location = await location_el.inner_text() if location_el else None

            content_el = await page.query_selector('#jobDescriptionText, .jobsearch-jobDescriptionText')
            description = await content_el.inner_text() if content_el else None

            salary_text = await self._extract_salary(page)
            salary_min, salary_max, currency = self._parse_salary(salary_text)

            job_type = await self._extract_job_type(page)

            external_id = self._extract_job_id(url)

            return RawJob(
                external_id=external_id,
                title=title.strip(),
                company_name=company_name.strip(),
                location=location.strip() if location else None,
                description=description,
                url=url,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=currency,
                job_type=job_type,
            )

        except Exception as e:
            logger.error(f"Error parsing Indeed job {url}: {e}")
            return None

    async def _extract_salary(self, page: Page) -> Optional[str]:
        salary_el = await page.query_selector('#salaryInfoAndJobType span, [data-testid="attribute_snippet_testid"]')
        if salary_el:
            text = await salary_el.inner_text()
            if "£" in text or "$" in text or "€" in text:
                return text
        return None

    async def _extract_job_type(self, page: Page) -> Optional[str]:
        type_el = await page.query_selector('#salaryInfoAndJobType, [data-testid="jobsearch-JobMetadataHeader-item"]')
        if type_el:
            text = (await type_el.inner_text()).lower()
            if "permanent" in text or "full-time" in text:
                return "permanent"
            elif "contract" in text or "temporary" in text:
                return "contract"
        return None

    def _parse_salary(self, salary_text: Optional[str]) -> tuple[Optional[int], Optional[int], Optional[str]]:
        if not salary_text:
            return None, None, None

        currency = "GBP" if "£" in salary_text else "EUR" if "€" in salary_text else "USD"

        cleaned = salary_text.replace(",", "").replace("K", "000").replace("k", "000")
        numbers = re.findall(r"\d+", cleaned)

        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1]), currency
        elif len(numbers) == 1:
            return int(numbers[0]), None, currency

        return None, None, None

    def _extract_job_id(self, url: str) -> str:
        # Handle both /rc/clk?jk=... and /viewjob?jk=... formats
        match = re.search(r"jk=([a-f0-9]+)", url)
        if match:
            return f"indeed_{match.group(1)}"

        return f"indeed_{abs(hash(url))}"
