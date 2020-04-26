import datetime
import re

from src.common.models.reservation import CsvModel


class EdogawaReservationModel(CsvModel):
    """
    reservation model for edogawa-ku
    written by 藪智明 2019-11-09
    """

    CSV_FILE = "src/edogawa/reservation.csv"

    def __init__(self):
        super().__init__(self.CSV_FILE)

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
                    day_of_the_week = header_row[2][k - 1]
                    res.append(
                        {
                            self.BUILDING: building,
                            self.INSTITUTION: institution,
                            self.DATE: f"{year}-{month}-{date}",
                            self.DAY_OF_THE_WEEK: day_of_the_week,
                            self.RESERVATION_STATUS: target_arr[k],
                            self.RESERVATION_DIVISION: reservation_division,
                        },
                    )
        return res

    def append(self, rows):
        new_data = self.to_dict_rows(rows)
        self.data.extend(new_data)
