import datetime
import logging

from models import reservation
from models import scraper

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)


def main(date=None):
    reservation_model = reservation.KoutouReservationModel()
    scraper_model = scraper.KoutouScraperModel(date, reservation_model)
    scraper_model.prepare_for_scraping()
    scraper_model.scraping()
    scraper_model.clear()
    reservation_model.copy()


if __name__ == "__main__":
    main()
