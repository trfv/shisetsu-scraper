# coding: utf-8
import time

from src.models import scraper, reservation

def main(date):
    start = time.time()
    reservation_model = reservation.ReservationModel()
    scraper_model = scraper.KoutouScraperModel(date, reservation_model)
    scraper_model.prepare_for_scraping()
    scraper_model.scraping()
    scraper_model.clear()
    reservation_model.save()
    end = time.time()
    print(f'it took {end - start} seconds.')