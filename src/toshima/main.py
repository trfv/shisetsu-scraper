import logging
import time

from models import reservation
from models import scraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main(date=None):
    logger.info("start scraping.")
    start = time.time()
    reservation_model = reservation.ToshimaReservationModel()
    scraper_model = scraper.ToshimaScraperModel(date, reservation_model)
    scraper_model.prepare_for_scraping()
    scraper_model.scraping()
    scraper_model.clear()
    reservation_model.copy()
    end = time.time()
    logger.info(f"finish scraping({(end - start):.2f} seconds took for scraping.")


if __name__ == "__main__":
    main()
