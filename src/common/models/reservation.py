import io
import os
import pathlib

import pandas as pd
import psycopg2

# FIXME ローカルで実行するときは、ここの第2引数を書き換える必要がある
DATABASE_URL = os.environ.get("DATABASE_URL", "")


class CsvModel:
    """
    CSVのカラム名を定義している\n
    self.dataに対し、scraperから書き込んでいき、最終的にdataをcsvに変換する
    """

    BUILDING = "building"
    INSTITUTION = "institution"
    DATE = "date"
    DAY_OF_THE_WEEK = "day_of_the_week"
    RESERVATION_DIVISION = "reservation_division"
    RESERVATION_STATUS = "reservation_status"
    CSV_FILE = "src/reservation.csv"

    def __init__(self, csv_file):
        self.data = []
        self.csv_file = csv_file
        self.columns = [
            self.BUILDING,
            self.INSTITUTION,
            self.DATE,
            self.DAY_OF_THE_WEEK,
            self.RESERVATION_DIVISION,
            self.RESERVATION_STATUS,
        ]
        if not os.path.exists(csv_file):
            pathlib.Path(csv_file).touch()

    def save(self):
        df = pd.DataFrame(data=self.data, columns=self.columns,)
        df.to_csv(self.csv_file, columns=self.columns)
        print(f"saved data to {self.csv_file}")

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
