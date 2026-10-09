# Первичные тесты автопарка, поездок, JSON и консольного меню.

from copy import deepcopy
from pathlib import Path

import pytest

from fleet import (
    add_car, add_driver, check_car_capacity, filter_cars_by_capacity,
    find_cars,
    get_service_status, sort_cars,
)
from main import main
from storage import load_data, load_json, save_change, save_json
from trips import (
    calculate_fuel, cancel_trip, check_trip, create_trip, is_car_available,
    is_driver_available,
)
from utils import input_date, input_int, input_number


def sample_data() -> dict:
    #независимые тестовые коллекции автомобилей, водителей и поездок
    cars, drivers, trips = {}, {}, []
    add_car(cars, "Lada Vesta", "А123ВС77", 4, 48000, 40000, 10000, 8.5)
    add_car(cars, "ГАЗель NEXT", "В456ЕК77", 12, 25000, 20000, 10000, 12.0)
    add_car(cars, "Lada Granta", "М789ОР77", 4, 50000, 40000, 10000, 7.5)
    add_driver(drivers, "Иванов Иван Иванович", True)
    add_driver(drivers, "Петров Петр Петрович", True)
    add_driver(drivers, "Сидоров Алексей Сергеевич", False)
    create_trip(cars, drivers, trips, 2, 2, "2026-11-10", 90, 8)
    return dict(cars=cars, drivers=drivers, trips=trips)


def store_sample(directory: Path) -> dict:
    #запись тестовых коллекций в отдельный временный каталог
    data = sample_data()
    for name, records in data.items():
        save_json(directory / f"{name}.json",
                  list(records.values()) if isinstance(records, dict)
                  else records)
    return data


def test_add_car() -> None:
    cars = {}
    car = add_car(cars, "Test", "т123ес77", 4, 1000, 0, 10000, 7.5)
    assert cars[1] == car
    assert car["plate"] == "Т123ЕС77"


def test_duplicate_plate_rejected() -> None:
    cars = sample_data()["cars"]
    with pytest.raises(ValueError, match="госномером"):
        add_car(cars, "Test", "а123вс77", 4, 1000, 0, 10000, 7.5)
    assert len(cars) == 3


def test_find_car_case_insensitive() -> None:
    cars = sample_data()["cars"]
    assert find_cars(cars, "VESTA")[0]["id"] == 1
    assert find_cars(cars, "а123")[0]["id"] == 1
    assert find_cars(cars, "неизвестная") == []


def test_capacity_and_filter() -> None:
    cars = sample_data()["cars"]
    assert check_car_capacity(cars, 1, 4)
    assert not check_car_capacity(cars, 1, 5)
    assert [car["id"] for car in filter_cars_by_capacity(cars, 8)] == [2]


def test_sort_does_not_change_collection() -> None:
    cars = sample_data()["cars"]
    original = deepcopy(cars)
    assert [car["id"] for car in sort_cars(cars)] == [1, 3, 2]
    assert cars == original


def test_pr1_scenario_preserved() -> None:
    data = sample_data()
    assert check_trip(data["cars"], data["drivers"], data["trips"],
                      1, 1, "2026-11-11", 120, 2) == "Поездка разрешена."
    assert calculate_fuel(120, 8.5) == pytest.approx(10.2)
    assert "2000 км" in get_service_status(48000, 40000, 10000, 120)


def test_car_and_driver_date_conflicts() -> None:
    data = sample_data()
    assert not is_car_available(data["trips"], 2, "2026-11-10")
    assert not is_driver_available(data["trips"], 2, "2026-11-10")
    assert is_car_available(data["trips"], 2, "2026-11-11")
    for car_id, driver_id in ((2, 1), (1, 2)):
        with pytest.raises(ValueError, match="запрещена"):
            create_trip(data["cars"], data["drivers"], data["trips"],
                        car_id, driver_id, "2026-11-10", 100, 2)
    assert len(data["trips"]) == 1


def test_service_threshold_and_cumulative_routes() -> None:
    data = sample_data()
    with pytest.raises(ValueError, match="порога ТО"):
        create_trip(data["cars"], data["drivers"], data["trips"],
                    1, 1, "2026-11-11", 2000, 2)
    trip = create_trip(data["cars"], data["drivers"], data["trips"],
                       1, 1, "2026-11-11", 1900, 2)
    with pytest.raises(ValueError, match="порога ТО"):
        create_trip(data["cars"], data["drivers"], data["trips"],
                    1, 1, "2026-11-12", 100, 2)
    cancel_trip(data["trips"], trip["id"])
    assert is_car_available(data["trips"], 1, "2026-11-11")


def test_capacity_permission_and_overdue_rejected() -> None:
    data = sample_data()
    for car_id, driver_id, passengers in ((1, 1, 5), (1, 3, 2), (3, 1, 2)):
        with pytest.raises(ValueError, match="запрещена"):
            create_trip(data["cars"], data["drivers"], data["trips"],
                        car_id, driver_id, "2026-11-11", 120, passengers)


def test_missing_ids_rejected() -> None:
    data = sample_data()
    with pytest.raises(KeyError):
        create_trip(data["cars"], data["drivers"], data["trips"],
                    999, 1, "2026-11-11", 120, 2)
    with pytest.raises(KeyError):
        cancel_trip(data["trips"], 999)


def test_json_roundtrip(tmp_path) -> None:
    data = store_sample(tmp_path)
    assert load_data(tmp_path) == data
    trip = create_trip(data["cars"], data["drivers"], data["trips"],
                       1, 1, "2026-11-11", 120, 2)
    save_json(tmp_path / "trips.json", data["trips"])
    restored = load_data(tmp_path)
    assert not is_car_available(restored["trips"], 1, "2026-11-11")
    cancel_trip(restored["trips"], trip["id"])
    save_json(tmp_path / "trips.json", restored["trips"])
    assert is_car_available(load_data(tmp_path)["trips"], 1, "2026-11-11")


def test_missing_file_is_empty(tmp_path) -> None:
    assert load_json(tmp_path / "missing.json") == []


def test_invalid_json_is_not_overwritten(tmp_path, capsys) -> None:
    filename = tmp_path / "cars.json"
    filename.write_text("{broken", encoding="utf-8")
    main(tmp_path)
    assert "Не удалось загрузить" in capsys.readouterr().out
    assert filename.read_text(encoding="utf-8") == "{broken"


def test_invalid_schema_rejected(tmp_path) -> None:
    save_json(tmp_path / "cars.json", [{"id": True}])
    with pytest.raises(ValueError):
        load_data(tmp_path)


def test_write_error_keeps_memory_and_file(tmp_path, monkeypatch) -> None:
    filename = tmp_path / "trips.json"
    save_json(filename, [{"id": 1}])
    old_contents = filename.read_bytes()
    data = {"trips": [{"id": 1}]}

    def reject_replace(*args):
        raise PermissionError("Запись запрещена")

    monkeypatch.setattr(Path, "replace", reject_replace)
    with pytest.raises(PermissionError):
        save_change(tmp_path, data, "trips", [{"id": 2}])
    assert data["trips"] == [{"id": 1}]
    assert filename.read_bytes() == old_contents
    assert not filename.with_suffix(".json.tmp").exists()


def test_safe_input_retries(monkeypatch) -> None:
    answers = iter(["буква", "0", "2", "2026-02-30", "2026-11-11",
                    "nan", "-1", "8,5"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert input_int("ID: ") == 2
    assert input_date("Дата: ") == "2026-11-11"
    assert input_number("Расход: ") == 8.5


def test_all_menu_items(tmp_path, monkeypatch, capsys) -> None:
    data = store_sample(tmp_path)
    answers = iter([
        "1", "2", "TestCar", "Т111ЕЕ77", "3", "100", "0", "10000", "6",
        "3", "test", "4", "4", "3", "5", "10", "6", "7",
        "8", "Тестовый Водитель", "да", "9", "4", "4", "2026-11-11",
        "10", "1", "1", "2026-11-11", "120", "2",
        "11", "4", "4", "2026-11-11", "50", "2", "13", "12", "2", "0",
    ])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    main(tmp_path)
    result = capsys.readouterr().out
    restored = load_data(tmp_path)
    assert len(restored["cars"]) == len(restored["drivers"]) == 4
    assert restored["trips"] == data["trips"]
    for expected in ("Поездка разрешена.", "10.2 л", "1880 км",
                     "Поездка создана", "Поездка отменена"):
        assert expected in result


def test_menu_recovers_from_unknown_choice_and_id(
        tmp_path, monkeypatch, capsys) -> None:
    store_sample(tmp_path)
    answers = iter(["буква", "4", "999", "2", "0"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    main(tmp_path)
    result = capsys.readouterr().out
    assert "Неизвестный пункт" in result
    assert "Запись с ID 999 не найдена" in result
    assert "Работа завершена" in result


def test_broken_reference_rejected(tmp_path) -> None:
    data = store_sample(tmp_path)
    data["trips"][0]["car_id"] = 999
    save_json(tmp_path / "trips.json", data["trips"])
    with pytest.raises(KeyError):
        load_data(tmp_path)


def test_duplicate_ids_rejected(tmp_path) -> None:
    save_json(tmp_path / "cars.json", [{"id": 1}, {"id": 1}])
    with pytest.raises(ValueError, match="Повтор ID"):
        load_data(tmp_path)
