import datetime
import io
import os
import pathlib
import re

import pandas as pd
import psycopg2

# FIXME ローカルで実行するときは、ここの第2引数を書き換える必要がある
DATABASE_URL = os.environ.get("DATABASE_URL", "")


class EdogawaReservationModel:
    """
    reservation model for edogawa-ku
    written by 藪智明 2019-11-09
    """

    BUILDING = "building"
    INSTITUTION = "institution"
    DATE = "date"
    DAY_OF_WEEK = "day_of_week"
    # FIXME reservation status と reservation division をまとめたカラムに変更されました。
    RESERVATION_DIVISION = "reservation_division"
    RESERVATION_STATUS = "reservation_status"
    CSV_FILE = "src/edogawa/reservation.csv"

    def __init__(self):
        self.data = []
        self.columns = [
            self.BUILDING,
            self.INSTITUTION,
            self.DATE,
            self.DAY_OF_WEEK,
            self.RESERVATION_DIVISION,
            self.RESERVATION_STATUS,
        ]
        if not os.path.exists(self.CSV_FILE):
            pathlib.Path(self.CSV_FILE).touch()

    def to_dict_rows(self, rows):
        res = []
        header_row = rows[0]  # [開始年月日, 日にち, 曜日]
        year = re.findall(r"\d{4}[/\.年]", header_row[0])[0].strip("年")
        month = re.findall(r"\d{2}[/\.月]", header_row[0])[0].strip("月")
        for i in range(1, len(rows)):
            target_institution = rows[i]
            [building, institution] = target_institution[0]
            print(f"start appending data for {building} {institution}")
            for j in range(1, len(target_institution)):
                target_arr = target_institution[j]
                reservation_division = target_arr[0]
                for k in range(1, len(target_arr)):
                    date = header_row[1][k - 1]
                    day_of_week = header_row[2][k - 1]
                    res.append(
                        {
                            self.BUILDING: building,
                            self.INSTITUTION: institution,
                            self.DATE: f"{year}-{month}-{date}",
                            self.DAY_OF_WEEK: day_of_week,
                            self.RESERVATION_STATUS: target_arr[k],
                            self.RESERVATION_DIVISION: reservation_division,
                        },
                    )
        return res

    def append(self, rows):
        new_data = self.to_dict_rows(rows)
        self.data.extend(new_data)

    def save(self):
        df = pd.DataFrame(data=self.data, columns=self.columns,)
        df.to_csv(self.csv_file, columns=self.columns)
        print(f"saved data to {self.csv_file}")
