import datetime
import io
import os
import pathlib

import pandas as pd
import psycopg2

# FIXME ローカルで実行するときは、ここの第2引数を書き換える必要がある
DATABASE_URL = os.environ.get("DATABASE_URL", "")


class KoutouReservationModel:
    """
     reservation model for koutou-ku
    """

    BUILDING = "building"
    INSTITUTION = "institution"
    DATE = "date"
    DAY_OF_THE_WEEK = "day_of_the_week"
    RESERVATION_DIVISION = "reservation_division"
    RESERVATION_STATUS = "reservation_status"
    CSV_FILE = "src/koutou/reservation.csv"

    def __init__(self):
        self.data = []
        self.columns = [
            self.BUILDING,
            self.INSTITUTION,
            self.DATE,
            self.DAY_OF_THE_WEEK,
            self.RESERVATION_DIVISION,
            self.RESERVATION_STATUS,
        ]
        if not os.path.exists(self.CSV_FILE):
            pathlib.Path(self.CSV_FILE).touch()

    def to_dict_rows(self, building, institution, rows):
        res = []
        header_row = rows[0]
        now = datetime.datetime.today()
        for i in range(1, len(rows)):
            target_row = rows[i]
            reservation_division = target_row[0]
            for j in range(1, len(target_row)):
                year = header_row[0].replace(" 年", "")
                [date, day_of_the_week] = (
                    header_row[j].replace("/", "-").replace(")", "").split("(")
                )
                res.append(
                    {
                        self.BUILDING: building,
                        self.INSTITUTION: institution,
                        self.DATE: f"{year}-{date}",
                        self.DAY_OF_THE_WEEK: day_of_the_week,
                        self.RESERVATION_STATUS: target_row[j],
                        self.RESERVATION_DIVISION: reservation_division,
                    },
                )
        return res

    def append(self, building, institution, rows):
        print(f"start appending data for {building} {institution}")
        new_data = self.to_dict_rows(building, institution, rows)
        self.data.extend(new_data)

    def copy(self):
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        cur = conn.cursor()

        f = io.StringIO()
        f.write(",".join(str(col) for col in self.columns) + "\n")
        f.write("\n".join(",".join(str(val) for val in d.values()) for d in self.data))
        f.seek(0)

        cur.execute("delete from reservation;")
        cur.copy_from(f, "reservation", sep=",", columns=self.columns)
        cur.close()
        conn.commit()
        print("copied data to database")
