import collections
import datetime
import os
import pandas as pd
import pathlib

class CsvModel():
    """
    base csv model.
    """
    def __init__(self, csv_file):
        self.csv_file = csv_file
        if not os.path.exists(csv_file):
            pathlib.Path(csv_file).touch()

class ReservationModel(CsvModel):
    """
    definition of class that generates reservation model for csv
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

    def __init__(self, csv_file=None):
        if not csv_file:
            csv_file = self.CSV_FILE
        super().__init__(csv_file)
        self.data = []

    def to_dict_rows(self, building, institution, rows):
        res = []
        header_row = rows[0]
        now = datetime.datetime.today()
        for i in range(1, len(rows)):
            target_row = rows[i]
            reservation_division = target_row[0]
            for j in range(1, len(target_row)):
                year = header_row[0].replace(' 年', '')
                [date, day_of_the_week] = header_row[j].replace('/','-').replace(')','').split('(')
                res.append({
                    self.BUILDING: building,
                    self.INSTITUTION: institution,
                    self.DATE: f'{year}-{date}',
                    self.DAY_OF_THE_WEEK: day_of_the_week,
                    self.RESERVATION_STATUS: target_row[j],
                    self.RESERVATION_DIVISION: reservation_division,
                    self.CREATE_DATETIME: now,
                    self.UPDATE_DATETIME: now,
                })
        return res

    def append(self, building, institution, rows):
        print(f'start appending data for {building} {institution}')
        new_data = self.to_dict_rows(building, institution, rows)
        self.data.extend(new_data)
    
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
