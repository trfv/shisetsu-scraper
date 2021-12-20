import enum
import io
import json
import os

import dotenv
import requests
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

dotenv.load_dotenv()
GRAPHQL_URL = os.environ.get("GRAPHQL_URL", "")
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "")
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
    res["prefecture"] = "PREFECTURE_TOKYO"
    res["municipality"] = tokyo_ward.replace("TOKYO_WARD", "MUNICIPALITY")
    for k, v in row.items():
        key = str(k)
        if key == "capacity" or key == "area":
            if v != "":
                res[key] = v
            else:
                res[key] = None
        elif key == "fee_divisions":
            if v:
                res["fee_divisions"] = (
                    "{"
                    + ",".join([FeeDivision.to_enum_value(t) for t in v.split(",")])
                    + "}"
                )
            else:
                res["fee_divisions"] = "{}"
        elif key.endswith("usage_fee"):
            tmp = []
            if v:
                for i in v.split(","):
                    x, y = i.split("=")
                    tmp.append({
                        "division": FeeDivision.to_enum_value(x),
                        "fee": int(y)
                    })
            res[key] = tmp
        elif key.startswith("is_available"):
            res[key] = AvailabilityDivision.to_enum_value(v) if v else ""
        elif key.startswith("is_equipped"):
            res[key] = EquipmentDivision.to_enum_value(v) if v else ""
        else:
            res[key] = v
    return res


COLUMNS = [
    "id",
    "prefecture",
    "municipality",
    "building",
    "institution",
    "building_kana",
    "institution_kana",
    "building_system_name",
    "institution_system_name",
    "capacity",
    "area",
    "fee_divisions",
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

AVAILABLE_MUNICIPALITIES = [
    "MUNICIPALITY_KOUTOU",
    "MUNICIPALITY_BUNKYO",
    "MUNICIPALITY_KITA",
    "MUNICIPALITY_TOSHIMA",
    "MUNICIPALITY_EDOGAWA",
    "MUNICIPALITY_ARAKAWA",
    "MUNICIPALITY_SUMIDA",
    "MUNICIPALITY_OTA",
    "MUNICIPALITY_SUGINAMI",
]


def main():
    data = []
    for municipality in AVAILABLE_MUNICIPALITIES:
        response = requests.get(
            f"{SHISETSU_APPS_SCRIPT_ENDPOINT}?tokyoWard={municipality}"
        )
        for row in response.json():
            new_data = to_dict(row, municipality)
            data.append(new_data)

    client = Client(
        transport=RequestsHTTPTransport(
            url = GRAPHQL_URL,
            use_json = True,
            headers = {
                "Content-type": "application/json",
                "X-Hasura-Admin-Secret": ADMIN_SECRET,
            },
            retries = 3,
        ),
        fetch_schema_from_transport=True,
    )
    client.execute(
        gql("""
            mutation update_institutions(
                $data: [institutions_insert_input!]!
                $columns: [institutions_update_column!]!
            ) {
                insert_institutions(
                    objects: $data,
                    on_conflict: {
                        constraint: institutions_id_key,
                        update_columns: $columns
                    }
                ) {
                    affected_rows
                }
            }"""
        ),
        variable_values={
            "data": data,
            "columns": COLUMNS
        }
    )


if __name__ == "__main__":
    main()
