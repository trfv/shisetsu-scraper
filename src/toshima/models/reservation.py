import datetime
import enum
import io
import json
import logging
import os
import time

import dotenv
import psycopg2

dotenv.load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

logger = logging.getLogger(__name__)

DEFAULT_UUID = "00000000-0000-0000-0000-000000000000"


class ReservationDivision(enum.Enum):
    INVALID = "RESERVATION_DIVISION_INVALID"
    MORNING = "RESERVATION_DIVISION_MORNING"
    AFTERNOON = "RESERVATION_DIVISION_AFTERNOON"
    EVENING = "RESERVATION_DIVISION_EVENING"


class DayOfWeek(enum.Enum):
    INVALID = "DAY_OF_WEEK_INVALID"
    SUNDAY = "DAY_OF_WEEK_SUNDAY"
    MONDAY = "DAY_OF_WEEK_MONDAY"
    TUESDAY = "DAY_OF_WEEK_TUESDAY"
    WEDNESDAY = "DAY_OF_WEEK_WEDNESDAY"
    THUESDAY = "DAY_OF_WEEK_THUESDAY"
    FRIDAY = "DAY_OF_WEEK_FRIDAY"
    SATURDAY = "DAY_OF_WEEK_SATURDAY"


class ToshimaReservationModel:
    """
    reservation model for toshima-ku
    """

    BUILDING = "building"
    INSTITUTION = "institution"
    DATE = "date"
    DAY_OF_WEEK = "day_of_week"
    RESERVATION = "reservation"
    INSTITUTION_ID = "institution_id"

    def __init__(self):
        self.data = {}
        self.columns = [
            self.BUILDING,
            self.INSTITUTION,
            self.DATE,
            self.DAY_OF_WEEK,
            self.RESERVATION,
            self.INSTITUTION_ID,
        ]

    def get_reservation_division_from_text(self, text):
        if text == "午前":
            return ReservationDivision.MORNING.value
        elif text == "午後":
            return ReservationDivision.AFTERNOON.value
        elif text == "夜間":
            return ReservationDivision.EVENING.value
        else:
            return ReservationDivision.INVALID.value

    def get_day_of_week_from_text(self, text):
        if text == "日":
            return DayOfWeek.SUNDAY.value
        elif text == "月":
            return DayOfWeek.MONDAY.value
        elif text == "火":
            return DayOfWeek.TUESDAY.value
        elif text == "水":
            return DayOfWeek.WEDNESDAY.value
        elif text == "木":
            return DayOfWeek.THUESDAY.value
        elif text == "金":
            return DayOfWeek.FRIDAY.value
        elif text == "土":
            return DayOfWeek.SATURDAY.value
        else:
            return DayOfWeek.INVALID.value

    def to_dict_rows(self, rows):
        # row: [buiding, institute, date, day_of_week, div, status]
        res = []
        for row in rows:
            building = row[0]
            institution = row[1]
            # yyyy/m/d という文字列を、yyyy, mm-dd に変換する
            year, m, d = row[2].split("/")
            date = f"{m.zfill(2)}-{d.zfill(2)}"
            day_of_week = row[3]
            # { 区分: 状態 } という dict を作成する（あとで結合する）
            reservation = {self.get_reservation_division_from_text(row[4]): row[5]}
            res.append(
                {
                    self.BUILDING: building,
                    self.INSTITUTION: institution,
                    self.DATE: f"{year}-{date}",
                    self.DAY_OF_WEEK: self.get_day_of_week_from_text(day_of_week),
                    self.RESERVATION: reservation,
                    self.INSTITUTION_ID: DEFAULT_UUID,
                },
            )
        return res

    def append(self, division, rows, month):
        building, institution, div = rows[0][0], rows[0][1], rows[0][4]
        logger.info(f"append data for {building} {institution} {div} (month{month})")
        new_data = self.to_dict_rows(rows)
        if division in self.data.keys():
            self.data[division].extend(new_data)
        else:
            self.data[division] = new_data

    def copy(self):
        combined = []
        div1, div2, div3 = self.data.values()
        for d1, d2, d3 in zip(div1, div2, div3):
            reservation = {
                **d1[self.RESERVATION],
                **d2[self.RESERVATION],
                **d3[self.RESERVATION],
            }
            combined.append(
                {
                    self.BUILDING: d1[self.BUILDING],
                    self.INSTITUTION: d1[self.INSTITUTION],
                    self.DATE: d1[self.DATE],
                    self.DAY_OF_WEEK: d1[self.DAY_OF_WEEK],
                    self.RESERVATION: json.dumps(reservation),
                    self.INSTITUTION_ID: d1[self.INSTITUTION_ID],
                }
            )
        f = io.StringIO()
        f.write(
            "\n".join(
                "\t".join(str(d.get(col)) for col in self.columns) for d in combined
            )
        )
        f.seek(0)

        logger.info("copy data to database")
        start = time.time()
        with psycopg2.connect(DATABASE_URL, sslmode="require") as conn:
            with conn.cursor() as cur:
                cur.execute("delete from reservation;")
                cur.copy_from(f, "reservation", sep="\t", columns=self.columns)

        end = time.time()
        logger.info(f"{(end - start):.2f} seconds took for copying.")
