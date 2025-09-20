import datetime
from pathlib import Path

from extraction.spiders.mercadolivre import MercadoLivreSpider
from transforms.data_transformation import transform_data

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def main():
    # Check if data.json exists
    data_path = DATA_DIR / "data.json"

    if data_path.exists():
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = DATA_DIR / f"data_{timestamp}.json"
        data_path.rename(new_name)
        print(f"Renamed existing data.json to data_{timestamp}.json")
    
    MercadoLivreSpider.run_spider()
    transform_data(DATA_DIR / "data.json")


if __name__ == "__main__":
    main()
