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


class FeeDivision(enum.Enum):
    INVALID = ("FEE_DIVISION_INVALID", None)
    MORNING = ("FEE_DIVISION_MORNING", "午前")
    AFTERNOON = ("FEE_DIVISION_AFTERNOON", "午後")
    AFTERNOON_ONE = ("FEE_DIVISION_AFTERNOON_ONE", "午後1")
    AFTERNOON_TWO = ("FEE_DIVISION_AFTERNOON_TWO", "午後2")
    EVENING = ("FEE_DIVISION_EVENING", "夜間")
    EVENING_ONE = ("FEE_DIVISION_EVENING_ONE", "夜間1")
    EVENING_TWO = ("FEE_DIVISION_EVENING_TWO", "夜間2")
    ONE_HOUR = ("FEE_DIVISION_ONE_HOUR", "1時間")
    DIVISION_1 = ("FEE_DIVISION_DIVISION_1", "①")
    DIVISION_2 = ("FEE_DIVISION_DIVISION_2", "②")
    DIVISION_3 = ("FEE_DIVISION_DIVISION_3", "③")
    DIVISION_4 = ("FEE_DIVISION_DIVISION_4", "④")
    DIVISION_5 = ("FEE_DIVISION_DIVISION_5", "⑤")
    DIVISION_6 = ("FEE_DIVISION_DIVISION_6", "⑥")

    def __init__(self, k, v):
        self.k = k
        self.v = v

    @classmethod
    def to_enum_value(cls, v):
        for c in [*cls.__members__.values()]:
            if v == c.v:
                return c.k
        return cls.INVALID.k


class AvailabilityDivision(enum.Enum):
    INVALID = ("AVAILABILITY_DIVISION_INVALID", None)
    AVAILABLE = ("AVAILABILITY_DIVISION_AVAILABLE", "利用可")
    UNAVAILABLE = ("AVAILABILITY_DIVISION_UNAVAILABLE", "利用不可")
    UNKNOWN = ("AVAILABILITY_DIVISION_UNKNOWN", "不明")

    def __init__(self, k, v):
        self.k = k
        self.v = v

    @classmethod
    def to_enum_value(cls, v):
        for c in [*cls.__members__.values()]:
            if v == c.v:
                return c.k
        return cls.INVALID.k


class EquipmentDivision(enum.Enum):
    INVALID = ("EQUIPMENT_DIVISION_INVALID", None)
    EQUIPPED = ("EQUIPMENT_DIVISION_EQUIPPED", "あり")
    UNEQUIPPED = ("EQUIPMENT_DIVISION_UNEQUIPPED", "なし")
    UNKNOWN = ("EQUIPMENT_DIVISION_UNKNOWN", "不明")

    def __init__(self, k, v):
        self.k = k
        self.v = v

    @classmethod
    def to_enum_value(cls, v):
        for c in [*cls.__members__.values()]:
            if v == c.v:
                return c.k
        return cls.INVALID.k


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
        elif key == "fee_division":
            if v:
                res[key] = (
                    "{"
                    + ",".join([FeeDivision.to_enum_value(t) for t in v.split(",")])
                    + "}"
                )
            else:
                res[key] = "{}"
        elif key.endswith("usage_fee"):
            tmp = {}
            if v:
                for i in v.split(","):
                    x, y = i.split("=")
                    tmp[FeeDivision.to_enum_value(x)] = y
            res[key] = json.dumps(tmp, ensure_ascii=False)
        elif key.startswith("is_available"):
            res[key] = AvailabilityDivision.to_enum_value(v) if v else ""
        elif key.startswith("is_equipped"):
            res[key] = EquipmentDivision.to_enum_value(v) if v else ""
        else:
            res[key] = v
    return res


COLUMNS = [
    "id",
    "tokyo_ward",
    "building",
    "institution",
    "building_system_name",
    "institution_system_name",
    "capacity",
    "area",
    "fee_division",
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

AVAILABLE_TOKYO_WARDS = [
    "TOKYO_WARD_KOUTOU",
    "TOKYO_WARD_BUNKYO",
    "TOKYO_WARD_KITA",
    "TOKYO_WARD_TOSHIMA",
    "TOKYO_WARD_EDOGAWA",
    "TOKYO_WARD_ARAKAWA",
]


def main():
    data = []
    for tokyo_ward in AVAILABLE_TOKYO_WARDS:
        response = requests.get(
            f"{SHISETSU_APPS_SCRIPT_ENDPOINT}?tokyoWard={tokyo_ward}"
        )
        for row in response.json():
            new_data = to_dict(row, tokyo_ward)
            data.append(new_data)

    f = io.StringIO()
    f.write("\n".join("\t".join(str(d.get(col)) for col in COLUMNS) for d in data))
    f.seek(0)

    with psycopg2.connect(DATABASE_URL, sslmode="require") as conn:
        with conn.cursor() as cur:
            cur.execute("truncate table institution restart identity;")
            cur.copy_from(f, "institution", sep="\t", columns=COLUMNS, null="None")


if __name__ == "__main__":
    main()
