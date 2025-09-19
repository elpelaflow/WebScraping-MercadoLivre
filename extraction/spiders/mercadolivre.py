import os
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from config_utils import load_search_query

save_path = os.path.join(os.getcwd(), 'data')

class MercadoLivreSpider(scrapy.Spider):
    name = "mercadolivre"
    allowed_domains = ["listado.mercadolibre.com.ar"]
    start_urls = [f"https://listado.mercadolibre.com.ar/{load_search_query()}"]

    page_count = 1
    max_pages = 20


    def parse(self, response):
        products = response.css('div.ui-search-result__wrapper')

        for product in products:
            # Mercado Livre stores multiple "prices" in this single span
            prices = product.css('span.andes-money-amount__fraction::text').getall()
            cents = product.css('span.andes-money-amount__cents::text').get()

            ad_label = product.css('.ui-search-item__ad-label::text, .ui-search-item__ad-badge::text').get()
            is_ad = bool(ad_label and ad_label.strip())

            price_value = None
            if prices:
                cents_value = cents.strip() if cents else "00"
                # Ensure the cents portion always contains two digits
                cents_value = cents_value.zfill(2)
                price_value = f"{prices[0]},{cents_value}"

            yield {
                'name': product.css('a.poly-component__title::text').get(),
                'seller': product.css('span.poly-component__seller::text').get(),
                'price': price_value,
                'reviews_rating_number': product.css('span.poly-reviews__rating::text').get(),
                'reviews_amount': product.css('span.poly-reviews__total::text').get(),
                'is_ad': is_ad
            }

        if self.page_count < self.max_pages:
            # 48 is the amount of items shown on a given page
            offset = 48 * self.page_count
            base_url = response.url.split('_Desde_')[0]
            next_page = f"{base_url}_Desde_{offset}"
            if next_page:
                self.page_count += 1
                yield scrapy.Request(url=next_page, callback=self.parse)


    def run_spider():
        os.makedirs(save_path, exist_ok=True)
        process = CrawlerProcess(settings={
            **get_project_settings(),
            "FEEDS": {
                os.path.join(save_path, 'data.json'): {
                    "format": "json",
                    "overwrite": True,
                }
            }
        })
        process.crawl(MercadoLivreSpider)
        process.start()
