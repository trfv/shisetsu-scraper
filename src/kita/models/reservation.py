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

tokyoWard = "TOKYO_WARD_KITA"


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


class KitaReservationModel:
    """
    reservation model for kita-ku
    """

    BUILDING = "building"
    INSTITUTION = "institution"
    DATE = "date"
    DAY_OF_WEEK = "day_of_week"
    RESERVATION = "reservation"
    INSTITUTION_ID = "institution_id"
    TOKYO_WARD = "tokyo_ward"

    def __init__(self):
        self.data = []
        self.columns = [
            self.INSTITUTION_ID,
            self.TOKYO_WARD,
            self.BUILDING,
            self.INSTITUTION,
            self.DATE,
            self.DAY_OF_WEEK,
            self.RESERVATION,
        ]

    def get_divisions_from_length(self, length):
        if length == 3:
            return [
                ReservationDivision.MORNING.value,
                ReservationDivision.AFTERNOON.value,
                ReservationDivision.EVENING.value,
            ]
        elif length == 5:
            return [
                ReservationDivision.ONE.value,
                ReservationDivision.TWO.value,
                ReservationDivision.THREE.value,
                ReservationDivision.FOUR.value,
                ReservationDivision.FIVE.value,
            ]
        else:
            raise Exception(f"unsupported division length: {length}")

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
        # row: [date, day_of_month, [div], [ReservationStatus]]
        res = []
        now = datetime.datetime.now()
        year = now.year
        for row in rows:
            # m/d という文字列を、mm-dd に変換する
            date = "-".join([s.zfill(2) for s in row[0].split("/")])
            # 今日が1月1日ではない時に1月1日以降のデータを扱うときは、yearを加算する
            if date == "01-01" and not (now.month == 1 and now.day == 1):
                year = year + 1
            day_of_week = row[1]
            # { 区分: 状態 } という dict を作成する
            divs = self.get_divisions_from_length(len(row[2]))
            reservation = dict(zip(divs, row[3]))
            res.append(
                {
                    self.INSTITUTION_ID: institution_id,
                    self.TOKYO_WARD: tokyoWard,
                    self.BUILDING: building,
                    self.INSTITUTION: institution,
                    self.DATE: f"{year}-{date}",
                    self.DAY_OF_WEEK: self.get_day_of_week_from_text(day_of_week),
                    self.RESERVATION: json.dumps(reservation),
                },
            )
        return res

    def append(self, building, institution, rows, institution_id, week):
        logger.debug(f"append data for {building} {institution} (week{week})")
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
                cur.execute(
                    f"delete from reservation where tokyo_ward = '{tokyoWard}';"
                )
                cur.copy_from(f, "reservation", sep="\t", columns=self.columns)

        end = time.time()
        logger.info(f"{(end - start):.2f} seconds took for copying.")
