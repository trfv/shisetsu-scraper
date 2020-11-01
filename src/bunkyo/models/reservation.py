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


class ReservationDivision(enum.Enum):
    INVALID = "RESERVATION_DIVISION_INVALID"
    MORNING = "RESERVATION_DIVISION_MORNING"
    AFTERNOON = "RESERVATION_DIVISION_AFTERNOON"
    EVENING = "RESERVATION_DIVISION_EVENING"
    ONE = "RESERVATION_DIVISION_ONE"
    TWO = "RESERVATION_DIVISION_TWO"
    THREE = "RESERVATION_DIVISION_THREE"
    FOUR = "RESERVATION_DIVISION_FOUR"
    FIVE = "RESERVATION_DIVISION_FIVE"


class DayOfWeek(enum.Enum):
    INVALID = "DAY_OF_WEEK_INVALID"
    SUNDAY = "DAY_OF_WEEK_SUNDAY"
    MONDAY = "DAY_OF_WEEK_MONDAY"
    TUESDAY = "DAY_OF_WEEK_TUESDAY"
    WEDNESDAY = "DAY_OF_WEEK_WEDNESDAY"
    THUESDAY = "DAY_OF_WEEK_THUESDAY"
    FRIDAY = "DAY_OF_WEEK_FRIDAY"
    SATURDAY = "DAY_OF_WEEK_SATURDAY"


class BunkyoReservationModel:
    """
    reservation model for bunkyo-ku
    """

    BUILDING = "building"
    INSTITUTION = "institution"
    DATE = "date"
    DAY_OF_WEEK = "day_of_week"
    RESERVATION = "reservation"
    INSTITUTION_ID = "institution_id"

    def __init__(self):
        self.data = []
        self.columns = [
            self.BUILDING,
            self.INSTITUTION,
            self.DATE,
            self.DAY_OF_WEEK,
            self.RESERVATION,
            self.INSTITUTION_ID,
        ]

    def get_division_from_text(self, text):
        if text == "午前":
            return ReservationDivision.MORNING.value
        elif text == "午後":
            return ReservationDivision.AFTERNOON.value
        elif text == "夜間":
            return ReservationDivision.EVENING.value
        elif text == "１コマ":
            return ReservationDivision.ONE.value
        elif text == "２コマ":
            return ReservationDivision.TWO.value
        elif text == "３コマ":
            return ReservationDivision.THREE.value
        elif text == "４コマ":
            return ReservationDivision.FOUR.value
        elif text == "５コマ":
            return ReservationDivision.FIVE.value
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

    def to_dict_rows(self, building, institution, rows, institution_id):
        # row: [year, date, day_of_month, [div], [ReservationStatus]]
        res = []

        for row in rows:
            year = row[0]
            # mm月dd日 という文字列を、mm-dd に変換する
            date = row[1].replace("月", "-").replace("日", "")
            # (X曜日) という文字列を X に変換する
            day_of_week = row[2][1:2]
            # { 区分: 状態 } という dict を作成する
            reservation = dict(
                zip([self.get_division_from_text(div) for div in row[3]], row[4])
            )
            res.append(
                {
                    self.BUILDING: building,
                    self.INSTITUTION: institution,
                    self.DATE: f"{year}-{date}",
                    self.DAY_OF_WEEK: self.get_day_of_week_from_text(day_of_week),
                    self.RESERVATION: json.dumps(reservation, ensure_ascii=False),
                    self.INSTITUTION_ID: institution_id,
                },
            )
        return res

    def append(self, building, institution, rows, institution_id, week):
        logger.info(f"append data for {building} {institution} (week{week})")
        new_data = self.to_dict_rows(building, institution, rows, institution_id)
        self.data.extend(new_data)

    def copy(self):
        f = io.StringIO()
        f.write(
            "\n".join(
                "\t".join(str(d.get(col)) for col in self.columns) for d in self.data
            )
        )
        f.seek(0)

        logger.info("copy data to database")
        start = time.time()
        with psycopg2.connect(DATABASE_URL, sslmode="require") as conn:
            with conn.cursor() as cur:
                cur.execute("truncate table reservation restart identity;")
                cur.copy_from(f, "reservation", sep="\t", columns=self.columns)

        end = time.time()
        logger.info(f"{(end - start):.2f} seconds took for copying.")
