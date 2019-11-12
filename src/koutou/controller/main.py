# coding: utf-8
import datetime

from src.koutou.models import scraper, reservation

def main(date):
    start = datetime.datetime.now()
    reservation_model = reservation.KoutouReservationModel('src/koutou/reservation.csv')
    scraper_model = scraper.KoutouScraperModel(date, reservation_model)
    scraper_model.prepare_for_scraping()
    scraper_model.scraping()
    scraper_model.clear()
    reservation_model.save()
    end = datetime.datetime.now()
    print(f'it took {end - start} seconds.')