from scrapers.sources.greenhouse import GreenhouseScraper
from scrapers.sources.lever import LeverScraper
from scrapers.sources.wttj import WTTJScraper
from scrapers.sources.indeed import IndeedScraper

SCRAPERS = {
    "greenhouse": GreenhouseScraper,
    "lever": LeverScraper,
    "wttj": WTTJScraper,
    "indeed": IndeedScraper,
}


def get_scraper(source_type: str, base_url: str, config: dict = None):
    scraper_class = SCRAPERS.get(source_type)
    if not scraper_class:
        raise ValueError(f"Unknown scraper type: {source_type}")
    return scraper_class(base_url=base_url, config=config)
