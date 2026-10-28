-- Предметная база автопарка. Все поля обязательны.
CREATE TABLE IF NOT EXISTS cars (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    model TEXT NOT NULL CHECK (length(trim(model)) > 0),
    plate TEXT NOT NULL UNIQUE CHECK (length(trim(plate)) > 0),
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    mileage INTEGER NOT NULL CHECK (mileage >= 0),
    fuel_consumption REAL NOT NULL CHECK (fuel_consumption > 0)
);

CREATE TABLE IF NOT EXISTS drivers (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    has_permission INTEGER NOT NULL CHECK (has_permission IN (0, 1))
);

CREATE TABLE IF NOT EXISTS maintenance (
    car_id INTEGER PRIMARY KEY REFERENCES cars(id),
    last_mileage INTEGER NOT NULL CHECK (last_mileage >= 0),
    interval INTEGER NOT NULL CHECK (interval > 0)
);

CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    car_id INTEGER NOT NULL REFERENCES cars(id),
    driver_id INTEGER NOT NULL REFERENCES drivers(id),
    trip_date TEXT NOT NULL CHECK (date(trip_date, '+0 days') IS trip_date),
    distance INTEGER NOT NULL CHECK (distance > 0),
    passengers INTEGER NOT NULL CHECK (passengers > 0),
    is_cancelled INTEGER NOT NULL DEFAULT 0 CHECK (is_cancelled IN (0, 1))
);

-- Отмена поездки освобождает автомобиль и водителя на эту дату.
CREATE UNIQUE INDEX IF NOT EXISTS active_trip_car_date
ON trips (car_id, trip_date) WHERE is_cancelled = 0;

CREATE UNIQUE INDEX IF NOT EXISTS active_trip_driver_date
ON trips (driver_id, trip_date) WHERE is_cancelled = 0;
