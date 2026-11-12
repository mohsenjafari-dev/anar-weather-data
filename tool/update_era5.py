
import calendar
import csv
import math
import os
import tempfile
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import cdsapi
import jdatetime
from eccodes import (
    codes_grib_new_from_file,
    codes_get,
    codes_get_array,
    codes_release,
)

UTC = timezone.utc
IRAN = timezone(timedelta(hours=3, minutes=30))
LAT, LON = 30.8739, 55.2708
AREA = [31.0, 55.1, 30.7, 55.5]
OUTPUT = Path("data/anar_latest.csv")


def read_grib(path, observations):
    with open(path, "rb") as file:
        while True:
            gid = codes_grib_new_from_file(file)
            if gid is None:
                break

            try:
                if codes_get(gid, "shortName") != "2t":
                    raise ValueError("Unexpected GRIB variable")

                d = int(codes_get(gid, "validityDate"))
                h = int(codes_get(gid, "validityTime"))
                timestamp = datetime.strptime(
                    f"{d}{h:04d}", "%Y%m%d%H%M"
                ).replace(tzinfo=UTC)

                lats = codes_get_array(gid, "latitudes")
                lons = codes_get_array(gid, "longitudes")
                temps = codes_get_array(gid, "values")

                weight = math.cos(math.radians(LAT)) ** 2
                nearest = min(
                    range(len(temps)),
                    key=lambda i: (
                        (lats[i] - LAT) ** 2
                        + weight * (lons[i] - LON) ** 2
                    ),
                )

                kelvin = float(temps[nearest])

                if not math.isfinite(kelvin) or not (
                    -60 <= kelvin - 273.15 <= 70
                ):
                    raise ValueError("Invalid temperature")

                if timestamp in observations:
                    raise ValueError("Duplicate timestamp")

                observations[timestamp] = kelvin
            finally:
                codes_release(gid)


def main():
    today = datetime.now(UTC).astimezone(IRAN).date()
    jalali = jdatetime.date.fromgregorian(date=today)
    season_year = (
        jalali.year if jalali.month >= 8
        else jalali.year - 1
    )

    start = jdatetime.date(
        season_year, 8, 15
    ).togregorian()

    spring = jdatetime.date(
        season_year + 1, 1, 1
    ).togregorian()

    # محافظه‌کارانه: درخواست تا ۵ روز پیش
    candidate_end = min(
        today - timedelta(days=5),
        spring - timedelta(days=1),
    )

    if candidate_end < start:
        print("No seasonal data available yet")
        return

    token = os.environ.get("CDSAPI_KEY")
    client = (
        cdsapi.Client(
            url="https://cds.climate.copernicus.eu/api",
            key=token,
        )
        if token else cdsapi.Client()
    )

    observations = {}

    with tempfile.TemporaryDirectory() as folder:
        cursor = start - timedelta(days=1)

        # دریافت ماه‌به‌ماه برای جلوگیری از درخواست بزرگ
        while cursor <= candidate_end:
            last_day = calendar.monthrange(
                cursor.year, cursor.month
            )[1]

            segment_end = min(
                candidate_end,
                date(cursor.year, cursor.month, last_day),
            )

            days = [
                f"{d:02d}"
                for d in range(
                    cursor.day, segment_end.day + 1
                )
            ]

            request = {
                "variable": ["2m_temperature"],
                "year": str(cursor.year),
                "month": f"{cursor.month:02d}",
                "day": days,
                "time": [
                    f"{h:02d}:00" for h in range(24)
                ],
                "data_format": "grib",
                "download_format": "unarchived",
                "area": AREA,
            }

            path = Path(folder) / (
                f"{cursor.year}_{cursor.month:02d}.grib"
            )

            client.retrieve(
                "reanalysis-era5-land",
                request,
                str(path),
            )

            read_grib(path, observations)
            cursor = segment_end + timedelta(days=1)

    # فقط روزهای کامل ایران از آغاز فصل انتخاب شوند
    records = []
    last_complete = None
    current = start

    while current <= candidate_end:
        midnight_utc = datetime.combine(
            current, time.min, tzinfo=IRAN
        ).astimezone(UTC)

        # نخستین ثبت ساعتی روز ایران: 00:30 ایران
        first_hour = midnight_utc + timedelta(minutes=30)

        hours = [
            first_hour + timedelta(hours=i)
            for i in range(24)
        ]

        if not all(hour in observations for hour in hours):
            break

        records.extend(
            (hour, observations[hour])
            for hour in hours
        )

        last_complete = current
        current += timedelta(days=1)

    if not records:
        print("No complete Iranian day available")
        return

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "valid_time", "t2m", "latitude", "longitude"
        ])

        for timestamp, kelvin in records:
            writer.writerow([
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                f"{kelvin:.5f}",
                "30.9",
                "55.3",
            ])

    print("ERA5 SEASON UPDATE OK")
    print("Season:", season_year)
    print("Last complete Iran day:", last_complete)
    print("Hourly records:", len(records))
    print("CSV:", OUTPUT)


if __name__ == "__main__":
    main()
