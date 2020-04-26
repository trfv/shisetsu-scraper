import datetime

from src.common.models.reservation import CsvModel


class KoutouReservationModel(CsvModel):
    """
     reservation model for koutou-ku
    """

    CSV_FILE = "src/koutou/reservation.csv"

    def __init__(self):
        super().__init__(self.CSV_FILE)

    def to_dict_rows(self, building, institution, rows):
        res = []
        header_row = rows[0]
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
