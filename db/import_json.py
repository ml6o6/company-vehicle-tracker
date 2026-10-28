"""Сформировать снимок базы автопарка из данных консольной версии."""

from contextlib import closing
from pathlib import Path

from storage import load_data

from .database import DB_PATH, SCHEMA_PATH, get_connection


def import_data(directory: Path = DB_PATH.parent, path: Path = DB_PATH
                ) -> tuple[int, int, int, int]:
    """Проверить исходные данные и заменить снимок одной транзакцией."""
    for name in ("cars.json", "drivers.json", "trips.json"):
        filename = directory / name
        if not filename.is_file():
            raise FileNotFoundError(filename)
    cars, drivers, trips = load_data(directory)
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    with closing(get_connection(path, write=True)) as conn, conn:
        conn.executescript("BEGIN IMMEDIATE;\n" + schema)
        conn.execute("DELETE FROM trips")
        conn.execute("DELETE FROM maintenance")
        conn.execute("DELETE FROM drivers")
        conn.execute("DELETE FROM cars")
        conn.executemany(
            """INSERT INTO cars
               (id, model, plate, capacity, mileage, fuel_consumption)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [(c.id, c.model, c.plate, c.capacity, c.mileage,
              c.fuel_consumption) for c in cars],
        )
        conn.executemany(
            """INSERT INTO drivers (id, name, has_permission)
               VALUES (?, ?, ?)""",
            [(d.id, d.name, int(d.has_permission)) for d in drivers],
        )
        conn.executemany(
            """INSERT INTO maintenance (car_id, last_mileage, interval)
               VALUES (?, ?, ?)""",
            [(c.id, c.maintenance.last_mileage, c.maintenance.interval)
             for c in cars],
        )
        conn.executemany(
            """INSERT INTO trips
               (id, car_id, driver_id, trip_date, distance, passengers,
                is_cancelled)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [(t.id, t.car.id, t.driver.id, t.trip_date, t.distance,
              t.passengers, int(t.is_cancelled)) for t in trips],
        )
        conn.commit()
    return len(cars), len(drivers), len(cars), len(trips)


if __name__ == "__main__":
    cars_count, drivers_count, maintenance_count, trips_count = import_data()
    print(f"Импортировано: автомобили — {cars_count}, "
          f"водители — {drivers_count}, ТО — {maintenance_count}, "
          f"поездки — {trips_count}.")
