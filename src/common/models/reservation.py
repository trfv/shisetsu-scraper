import os
import pandas as pd
import pathlib

class CsvModel():
    """
    base csv model
    """
    BUILDING = 'building'
    INSTITUTION = 'institution'
    DATE = 'date'
    DAY_OF_THE_WEEK = 'day_of_the_week'
    RESERVATION_DIVISION = 'reservation_division'
    RESERVATION_STATUS = 'reservation_status'
    CREATE_DATETIME = 'create_datetime'
    UPDATE_DATETIME = 'update_datetime'
    CSV_FILE = 'src/reservation.csv'

    def __init__(self, csv_file):
        self.data = []
        self.csv_file = csv_file
        if not os.path.exists(csv_file):
            pathlib.Path(csv_file).touch()
    
    def save(self):
        df = pd.DataFrame(
            data=self.data,
            columns=[
                self.BUILDING,
                self.INSTITUTION,
                self.DATE,
                self.DAY_OF_THE_WEEK,
                self.RESERVATION_DIVISION,
                self.RESERVATION_STATUS,
                self.CREATE_DATETIME,
                self.UPDATE_DATETIME,
            ]
        )
        df.to_csv(self.csv_file)