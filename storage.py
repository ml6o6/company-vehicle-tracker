#Загрузка и сохранение коллекций JSON с проверкой целостности.

import json
from pathlib import Path

from fleet import validate_car, validate_driver
from trips import create_trip
from utils import require_int


def load_json(filename: Path) -> list[dict]:
    #Прочитать список записей; отсутствие файла означает пустой список.
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


def index_records(records: list[dict]) -> dict[int, dict]:
    """Построить словарь по положительным ID; запретить повтор ID."""
    indexed = {}
    for record in records:
        record_id = require_int(record["id"], "ID записи", 1)
        if record_id in indexed:
            raise ValueError(f"Повтор ID: {record_id}.")
        indexed[record_id] = record
    return indexed


def load_data(directory: Path) -> dict:
    """Восстановить коллекции; проверить поля, связи и доступность."""
    cars = index_records(load_json(directory / "cars.json"))
    drivers = index_records(load_json(directory / "drivers.json"))
    trips = load_json(directory / "trips.json")
    for car in cars.values():
        validate_car(car)
    plates = [car["plate"].strip().casefold() for car in cars.values()]
    if len(set(plates)) != len(plates):
        raise ValueError("В файле автомобилей повторяются госномера.")
    for driver in drivers.values():
        validate_driver(driver)
    index_records(trips)
    checked = []
    for trip in trips:
        created = create_trip(
            cars, drivers, checked, trip["car_id"], trip["driver_id"],
            trip["trip_date"], trip["distance"], trip["passengers"],
        )
        created["id"] = trip["id"]
    return dict(cars=cars, drivers=drivers, trips=trips)


def save_change(directory: Path, data: dict, collection: str,
                candidate: dict | list) -> None:
    """Сначала сохранить измененную коллекцию, затем обновить память."""
    records = (list(candidate.values())
               if isinstance(candidate, dict) else candidate)
    save_json(directory / f"{collection}.json", records)
    data[collection] = candidate
