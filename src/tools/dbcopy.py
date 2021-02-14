import enum
import io
import json
import os

import dotenv
import psycopg2
import requests

dotenv.load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")
SHISETSU_APPS_SCRIPT_ENDPOINT = os.environ.get("SHISETSU_APPS_SCRIPT_ENDPOINT")

# the same as institution.sql
columns = [
    "id",
    "tokyo_ward",
    "building",
    "institution",
    "capacity",
    "area",
    "reservation_division",
    "weekday_usage_fee",
    "holiday_usage_fee",
    "address",
    "is_available_strings",
    "is_available_woodwind",
    "is_available_brass",
    "is_available_percussion",
    "is_equipped_music_stand",
    "is_equipped_piano",
    "website_url",
    "layout_image_url",
    "lottery_period",
    "note",
]


class ReservationDivision(enum.Enum):
    INVALID = "RESERVATION_DIVISION_INVALID"
    MORNING = "RESERVATION_DIVISION_MORNING"
    AFTERNOON = "RESERVATION_DIVISION_AFTERNOON"
    AFTERNOON_ONE = "RESERVATION_DIVISION_AFTERNOON_ONE"
    AFTERNOON_TWO = "RESERVATION_DIVISION_AFTERNOON_TWO"
    EVENING = "RESERVATION_DIVISION_EVENING"
    ONE = "RESERVATION_DIVISION_ONE"
    TWO = "RESERVATION_DIVISION_TWO"
    THREE = "RESERVATION_DIVISION_THREE"
    FOUR = "RESERVATION_DIVISION_FOUR"
    FIVE = "RESERVATION_DIVISION_FIVE"
    SIX = "RESERVATION_DIVISION_SIX"
    ONE_HOUR = "RESERVATION_DIVISION_ONE_HOUR"
    TWO_HOUR = "RESERVATION_DIVISION_TWO_HOUR"


def get_reservation_division_from_text(text):
    if text == "午前":
        return ReservationDivision.MORNING.value
    elif text == "午後":
        return ReservationDivision.AFTERNOON.value
    elif text == "午後1":
        return ReservationDivision.AFTERNOON_ONE.value
    elif text == "午後2":
        return ReservationDivision.AFTERNOON_TWO.value
    elif text == "夜間":
        return ReservationDivision.EVENING.value
    elif text == "①":
        return ReservationDivision.ONE.value
    elif text == "②":
        return ReservationDivision.TWO.value
    elif text == "③":
        return ReservationDivision.THREE.value
    elif text == "④":
        return ReservationDivision.FOUR.value
    elif text == "⑤":
        return ReservationDivision.FIVE.value
    elif text == "⑥":
        return ReservationDivision.SIX.value
    elif text == "1時間":
        return ReservationDivision.ONE_HOUR.value
    elif text == "2時間":
        return ReservationDivision.TWO_HOUR.value
    else:
        return ReservationDivision.INVALID.value


class AvailabilityDivision(enum.Enum):
    INVALID = "AVAILABILITY_DIVISION_INVALID"
    AVAILABLE = "AVAILABILITY_DIVISION_AVAILABLE"
    UNAVAILABLE = "AVAILABILITY_DIVISION_UNAVAILABLE"
    UNKNOWN = "AVAILABILITY_DIVISION_UNKNOWN"


def get_availability_division_from_text(text):
    if text == "利用可":
        return AvailabilityDivision.AVAILABLE.value
    if text == "利用不可":
        return AvailabilityDivision.UNAVAILABLE.value
    if text == "不明":
        return AvailabilityDivision.UNKNOWN.value
    else:
        return AvailabilityDivision.INVALID


class EquipmentDivision(enum.Enum):
    INVALID = "EQUIPMENT_DIVISION_INVALID"
    EQUIPPED = "EQUIPMENT_DIVISION_EQUIPPED"
    UNEQUIPPED = "EQUIPMENT_DIVISION_UNEQUIPPED"
    UNKNOWN = "EQUIPMENT_DIVISION_UNKNOWN"


def get_equipment_division_from_text(text):
    if text == "あり":
        return EquipmentDivision.EQUIPPED.value
    if text == "なし":
        return EquipmentDivision.UNEQUIPPED.value
    if text == "不明":
        return EquipmentDivision.UNKNOWN.value
    else:
        return EquipmentDivision.INVALID


def to_dict(row, tokyo_ward):
    res = {}
    res["tokyo_ward"] = tokyo_ward
    for k, v in row.items():
        key = str(k)
        if key == "capacity" or key == "area":
            if v != "":
                res[key] = v
            else:
                res[key] = None
        elif key == "reservation_division":
            if v:
                res[key] = (
                    "{"
                    + ",".join(
                        [get_reservation_division_from_text(t) for t in v.split(",")]
                    )
                    + "}"
                )
            else:
                res[key] = "{}"
        elif key.endswith("usage_fee"):
            tmp = {}
            if v:
                for i in v.split(","):
                    x, y = i.split("=")
                    tmp[get_reservation_division_from_text(x)] = y
            res[key] = json.dumps(tmp, ensure_ascii=False)
        elif key.startswith("is_available"):
            res[key] = get_availability_division_from_text(v) if v else ""
        elif key.startswith("is_equipped"):
            res[key] = get_equipment_division_from_text(v) if v else ""
        else:
            res[key] = v
    return res


# sheet types
types = [
    "TOKYO_WARD_KOUTOU",
    "TOKYO_WARD_BUNKYO",
    "TOKYO_WARD_KITA",
    "TOKYO_WARD_TOSHIMA",
]


def main():
    data = []
    for tokyo_ward in types:
        response = requests.get(
            f"{SHISETSU_APPS_SCRIPT_ENDPOINT}?tokyoWard={tokyo_ward}"
        )
        for row in response.json():
            new_data = to_dict(row, tokyo_ward)
            data.append(new_data)

    f = io.StringIO()
    f.write("\n".join("\t".join(str(d.get(col)) for col in columns) for d in data))
    f.seek(0)

    with psycopg2.connect(DATABASE_URL, sslmode="require") as conn:
        with conn.cursor() as cur:
            cur.execute("truncate table institution restart identity;")
            cur.copy_from(f, "institution", sep="\t", columns=columns, null="None")


if __name__ == "__main__":
    main()
