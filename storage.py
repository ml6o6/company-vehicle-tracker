"""Преобразование JSON в объекты и сохранение связей по ID."""

import json
from pathlib import Path

from models import Car, Driver, Trip
from models.cars import find_car_by_id
from models.drivers import find_driver_by_id
from models.trips import ALLOWED, check_trip


def load_json(filename: Path) -> list[dict]:
    """Прочитать список записей; отсутствие файла означает пустой список."""
    try:
        with filename.open(encoding="utf-8") as stream:
            records = json.load(stream)
    except FileNotFoundError:
        print(f"Файл {filename.name} отсутствует: загружен пустой список.")
        return []
    if not isinstance(records, list) or any(
            not isinstance(record, dict) for record in records):
        raise ValueError(f"{filename.name}: ожидается список словарей.")
    return records


def save_json(filename: Path, records: list[dict]) -> None:
    """Сохранить JSON через временный файл, защищая старые данные."""
    filename.parent.mkdir(parents=True, exist_ok=True)
    temporary = filename.with_suffix(".json.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(records, stream, ensure_ascii=False, indent=2,
                      allow_nan=False)
            stream.write("\n")
        temporary.replace(filename)
    finally:
        temporary.unlink(missing_ok=True)


def check_unique_ids(objects: list[Car] | list[Driver] | list[Trip]) -> None:
    """Запретить повтор идентификаторов в одной коллекции объектов."""
    ids = [item.id for item in objects]
    if len(set(ids)) != len(ids):
        raise ValueError("Повтор ID в файле данных.")


def load_cars(filename: Path) -> list[Car]:
    """Восстановить автомобили вместе с их объектами обслуживания."""
    cars = [Car.from_data(record) for record in load_json(filename)]
    check_unique_ids(cars)
    plates = [car.plate.casefold() for car in cars]
    if len(set(plates)) != len(plates):
        raise ValueError("В файле автомобилей повторяются госномера.")
    return cars


def load_drivers(filename: Path) -> list[Driver]:
    """Восстановить водителей через фабричный метод класса."""
    drivers = [Driver.from_data(record) for record in load_json(filename)]
    check_unique_ids(drivers)
    return drivers


def load_trips(filename: Path, cars: list[Car],
               drivers: list[Driver]) -> list[Trip]:
    """Восстановить ссылки на существующие объекты и состояние отмены."""
    trips = []
    for record in load_json(filename):
        car = find_car_by_id(cars, record["car_id"])
        driver = find_driver_by_id(drivers, record["driver_id"])
        trip = Trip(record["id"], car, driver, record["trip_date"],
                    record["distance"], record["passengers"],
                    record.get("is_cancelled", False))
        if not trip.is_cancelled:
            status = check_trip(trips, car, driver, trip.trip_date,
                                trip.distance, trip.passengers)
            if status != ALLOWED:
                raise ValueError(f"Поездка {trip.id}: {status}")
        trips.append(trip)
    check_unique_ids(trips)
    return trips


def load_data(directory: Path) -> tuple[list[Car], list[Driver], list[Trip]]:
    """Сначала загрузить участников, затем восстановить связанные поездки."""
    cars = load_cars(directory / "cars.json")
    drivers = load_drivers(directory / "drivers.json")
    trips = load_trips(directory / "trips.json", cars, drivers)
    return cars, drivers, trips


def save_cars(filename: Path, cars: list[Car]) -> None:
    """Сохранить автомобили в совместимом с ПР2 формате."""
    records = [dict(id=car.id, model=car.model, plate=car.plate,
                    capacity=car.capacity, mileage=car.mileage,
                    last_service_mileage=car.maintenance.last_mileage,
                    service_interval=car.maintenance.interval,
                    fuel_consumption=car.fuel_consumption) for car in cars]
    save_json(filename, records)


def save_drivers(filename: Path, drivers: list[Driver]) -> None:
    """Сохранить необходимые поля объектов водителей."""
    records = [dict(id=driver.id, name=driver.name,
                    has_permission=driver.has_permission)
               for driver in drivers]
    save_json(filename, records)


def save_trips(filename: Path, trips: list[Trip]) -> None:
    """Сохранить ID участников и признак отмены, без вложенных объектов."""
    records = [dict(id=trip.id, car_id=trip.car.id, driver_id=trip.driver.id,
                    trip_date=trip.trip_date, distance=trip.distance,
                    passengers=trip.passengers, is_cancelled=trip.is_cancelled)
               for trip in trips]
    save_json(filename, records)
