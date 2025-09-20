import re
from pathlib import Path

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from config_utils import load_max_pages, load_search_query

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

class MercadoLivreSpider(scrapy.Spider):
    name = "mercadolivre"
    allowed_domains = ["listado.mercadolibre.com.ar", "www.mercadolibre.com.ar"]

    page_count = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        search_query = load_search_query()
        self.start_urls = [f"https://listado.mercadolibre.com.ar/{search_query}"]
        self.max_pages = load_max_pages()
        self.page_count = 1

    def parse(self, response):
        products = response.css("li.ui-search-layout__item")
        if not products:
            products = response.css("div.ui-search-result__wrapper, [data-testid='item']")

        for product in products:
            link = product.css(
                "a.ui-search-item__group__element::attr(href), "
                "a.ui-search-link::attr(href), "
                "a.poly-component__link::attr(href), "
                "a::attr(href)"
            ).get()
            permalink = response.urljoin(link) if link else None
            ml_item_id = None
            if link:
                match = re.search(r"/MLA-?(\d+)", link)
                if match:
                    ml_item_id = f"MLA{match.group(1)}"

            name = product.css(
                "h2.ui-search-item__title::text, "
                "h2.ui-search-item__title span::text, "
                "a.poly-component__title::text, "
                "[data-testid='item-title']::text"
            ).get()
            name = name.strip() if name else None

            seller_texts = product.css(
                "[data-testid='seller-info'] ::text, "
                "span.poly-component__seller::text, "
                "span.ui-search-official-store-label__text::text"
            ).getall()
            seller = "".join(seller_texts).strip() if seller_texts else None
            if seller and seller.lower().startswith("por "):
                seller = seller[4:].strip()

            fraction = product.css("span.andes-money-amount__fraction::text").get()
            cents = product.css("span.andes-money-amount__cents::text").get()
            price_value = None
            if fraction:
                cents_value = cents.strip() if cents else "00"
                cents_value = cents_value.zfill(2)
                price_value = f"{fraction},{cents_value}"

            ad_markers = product.css(
                "[data-testid*='advertising'], "
                "[aria-label*='Promocionado' i], "
                "[data-testid*='sponsored'], "
                "[data-testid='listing-type-highlight']::text, "
                "[data-testid='listing-highlight-label']::text, "
                ".ui-search-item__ad-badge::text"
            ).getall()
            ad_texts = [marker.strip() for marker in ad_markers if marker and marker.strip()]
            is_ad = bool(ad_texts)

            yield {
                "ml_item_id": ml_item_id,
                "name": name,
                "seller": seller,
                "price": price_value,
                "permalink": permalink,
                "is_ad": is_ad,
            }

        if self.page_count < self.max_pages:
            next_page = response.css("a[rel='next']::attr(href), a[title='Siguiente']::attr(href)").get()
            if next_page:
                self.page_count += 1
                yield response.follow(next_page, callback=self.parse)


    def run_spider():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        process = CrawlerProcess(settings={
            **get_project_settings(),
            "FEEDS": {
                str(DATA_DIR / "data.json"): {
                    "format": "json",
                    "overwrite": True,
                }
            }
        })
        process.crawl(MercadoLivreSpider)
        process.start()
