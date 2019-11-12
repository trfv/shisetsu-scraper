# coding: utf-8
import datetime

from src.edogawa.models import reservation
from src.edogawa.models import scraper


def main(date):
    start = datetime.datetime.now()
    reservation_model = reservation.EdogawaReservationModel(
        "src/edogawa/reservation.csv",
    )
    scraper_model = scraper.EdogawaScraperModel(date, reservation_model)
    scraper_model.prepare_for_scraping()
    scraper_model.scraping()
    scraper_model.clear()
    reservation_model.save()
    end = datetime.datetime.now()
    print(f"it took {end - start} seconds.")
