import datetime

from src.koutou.models import reservation
from src.koutou.models import scraper


def main(date=None):
    if not date:
        date = datetime.date.today() + datetime.timedelta(days=1)
    reservation_model = reservation.KoutouReservationModel()
    scraper_model = scraper.KoutouScraperModel(date, reservation_model)
    scraper_model.prepare_for_scraping()
    scraper_model.scraping()
    scraper_model.clear()
    reservation_model.copy()


if __name__ == "__main__":
    main()
