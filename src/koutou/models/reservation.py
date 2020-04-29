import datetime
import decimal
import io
import json
import os
import pathlib
import time

import dotenv
import psycopg2

dotenv.load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")


class KoutouReservationModel:
    """
     reservation model for koutou-ku
    """

    BUILDING = "building"
    INSTITUTION = "institution"
    DATE = "date"
    DAY_OF_WEEK = "day_of_week"
    RESERVATION = "reservation"

    def __init__(self):
        self.data = []
        self.columns = [
            self.BUILDING,
            self.INSTITUTION,
            self.DATE,
            self.DAY_OF_WEEK,
            self.RESERVATION,
        ]

    def to_dict_rows(self, building, institution, rows):
        res = []
        header_row = rows[0]
        # XXXX 年 という文字列から XXXX を取り出す
        year = header_row[0].replace(" 年", "")

        for i in range(1, len(header_row)):
            # mm/dd(D) という文字列から、mm-dd と D を取り出す
            [date, day_of_week] = (
                header_row[i].replace("/", "-").replace(")", "").split("(")
            )
            # { 区分: 状態 } という dict を作成する
            reservation = {row[0]: row[i] for row in rows[1:]}
            res.append(
                {
                    self.BUILDING: building,
                    self.INSTITUTION: institution,
                    self.DATE: f"{year}-{date}",
                    self.DAY_OF_WEEK: day_of_week,
                    self.RESERVATION: json.dumps(reservation, ensure_ascii=False),
                },
            )
        return res

    def append(self, building, institution, rows):
        print(f"append data for {building} {institution}")
        new_data = self.to_dict_rows(building, institution, rows)
        self.data.extend(new_data)

    def copy(self):
        f = io.StringIO()
        f.write(
            "\n".join(
                "\t".join(str(d.get(col)) for col in self.columns) for d in self.data
            )
        )
        f.seek(0)

        print("copy data to database")
        start = time.time()
        with psycopg2.connect(DATABASE_URL, sslmode="require") as conn:
            with conn.cursor() as cur:
                cur.execute("delete from reservation;")
                cur.copy_from(f, "reservation", sep="\t", columns=self.columns)

        end = time.time()
        print(f"{end - start} seconds took for copying.")
