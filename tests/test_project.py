"""Сохраненные сценарии ПР2 и проверки объектной модели ПР3."""

from pathlib import Path

import pytest

from main import cancel_saved_trip, handle_action, main
from models import Car, Driver, Maintenance, Trip
from models.cars import (
    add_car, check_car_capacity, filter_cars_by_capacity, find_car_by_id,
    find_cars, sort_cars,
)
from models.drivers import add_driver
from models.trips import (
    cancel_trip, check_trip, create_trip, is_car_available,
    is_driver_available, reserved_distance,
)
from storage import (
    load_data, load_json, save_cars, save_drivers, save_json, save_trips,
)
from utils import input_date, input_int, input_number


def sample_data() -> tuple[list[Car], list[Driver], list[Trip]]:
    """Создать независимые коллекции объектов для сценариев ПР2."""
    cars, drivers, trips = [], [], []
    add_car(cars, "Lada Vesta", "А123ВС77", 4, 48000, 40000, 10000, 8.5)
    add_car(cars, "ГАЗель NEXT", "В456ЕК77", 12, 25000, 20000, 10000, 12.0)
    add_car(cars, "Lada Granta", "М789ОР77", 4, 50000, 40000, 10000, 7.5)
    add_driver(drivers, "Иванов Иван Иванович", True)
    add_driver(drivers, "Петров Петр Петрович", True)
    add_driver(drivers, "Сидоров Алексей Сергеевич", False)
    create_trip(trips, cars[1], drivers[1], "2026-11-10", 90, 8)
    return cars, drivers, trips


def store_sample(directory: Path
                 ) -> tuple[list[Car], list[Driver], list[Trip]]:
    """Сохранить подготовленные объекты только во временный каталог."""
    cars, drivers, trips = sample_data()
    save_cars(directory / "cars.json", cars)
    save_drivers(directory / "drivers.json", drivers)
    save_trips(directory / "trips.json", trips)
    return cars, drivers, trips


def test_add_car() -> None:
    cars = []
    car = add_car(cars, "Test", "т123ес77", 4, 1000, 0, 10000, 7.5)
    assert isinstance(car, Car)
    assert cars[0] is car
    assert car.plate == "Т123ЕС77"


def test_duplicate_plate_rejected() -> None:
    cars, _, _ = sample_data()
    with pytest.raises(ValueError, match="госномером"):
        add_car(cars, "Test", "а123вс77", 4, 1000, 0, 10000, 7.5)
    assert len(cars) == 3


def test_find_car_case_insensitive() -> None:
    cars, _, _ = sample_data()
    assert find_cars(cars, "VESTA")[0] is cars[0]
    assert find_cars(cars, "а123")[0] is cars[0]
    assert find_cars(cars, "неизвестная") == []


def test_capacity_and_filter() -> None:
    cars, _, _ = sample_data()
    assert check_car_capacity(cars, 1, 4)
    assert not check_car_capacity(cars, 1, 5)
    assert filter_cars_by_capacity(cars, 8) == [cars[1]]


def test_sort_does_not_change_collection() -> None:
    cars, _, _ = sample_data()
    original = list(cars)
    assert [car.id for car in sort_cars(cars)] == [1, 3, 2]
    assert cars == original


def test_pr1_scenario_preserved() -> None:
    cars, drivers, trips = sample_data()
    assert check_trip(trips, cars[0], drivers[0], "2026-11-11", 120, 2
                      ) == "Поездка разрешена."
    assert cars[0].calculate_fuel(120) == pytest.approx(10.2)
    assert "2000 км" in cars[0].get_service_status(120)


def test_car_and_driver_date_conflicts() -> None:
    cars, drivers, trips = sample_data()
    assert not is_car_available(trips, cars[1], "2026-11-10")
    assert not is_driver_available(trips, drivers[1], "2026-11-10")
    assert is_car_available(trips, cars[1], "2026-11-11")
    for car, driver in ((cars[1], drivers[0]), (cars[0], drivers[1])):
        assert create_trip(trips, car, driver, "2026-11-10", 100, 2) is None
    assert len(trips) == 1


def test_service_threshold_and_cumulative_routes() -> None:
    cars, drivers, trips = sample_data()
    car, driver = cars[0], drivers[0]
    assert create_trip(trips, car, driver, "2026-11-11", 2000, 2) is None
    trip = create_trip(trips, car, driver, "2026-11-11", 1900, 2)
    assert trip is not None
    assert create_trip(trips, car, driver, "2026-11-12", 100, 2) is None
    cancel_trip(trips, trip.id)
    assert trip in trips and trip.is_cancelled
    assert is_car_available(trips, car, "2026-11-11")
    assert reserved_distance(trips, car) == 0


def test_capacity_permission_and_overdue_rejected() -> None:
    cars, drivers, trips = sample_data()
    for car, driver, passengers in ((cars[0], drivers[0], 5),
                                    (cars[0], drivers[2], 2),
                                    (cars[2], drivers[0], 2)):
        assert create_trip(trips, car, driver, "2026-11-11", 120,
                           passengers) is None


def test_missing_ids_rejected() -> None:
    cars, _, trips = sample_data()
    with pytest.raises(KeyError):
        find_car_by_id(cars, 999)
    with pytest.raises(KeyError):
        cancel_trip(trips, 999)


def test_json_roundtrip(tmp_path) -> None:
    cars, drivers, trips = store_sample(tmp_path)
    restored_cars, restored_drivers, restored_trips = load_data(tmp_path)
    assert restored_trips[0].car is restored_cars[1]
    assert restored_trips[0].driver is restored_drivers[1]
    assert str(restored_cars[0]) == str(cars[0])
    assert str(restored_trips[0]) == str(trips[0])
    trip = create_trip(trips, cars[0], drivers[0], "2026-11-11", 120, 2)
    save_trips(tmp_path / "trips.json", trips)
    cars, drivers, trips = load_data(tmp_path)
    assert not is_car_available(trips, cars[0], "2026-11-11")
    cancel_trip(trips, trip.id)
    save_trips(tmp_path / "trips.json", trips)
    cars, drivers, trips = load_data(tmp_path)
    assert trips[-1].is_cancelled
    assert is_car_available(trips, cars[0], "2026-11-11")


def test_missing_file_is_empty(tmp_path) -> None:
    assert load_json(tmp_path / "missing.json") == []


def test_invalid_json_is_not_overwritten(tmp_path, capsys) -> None:
    filename = tmp_path / "cars.json"
    filename.write_text("{broken", encoding="utf-8")
    main(tmp_path)
    assert "Не удалось загрузить" in capsys.readouterr().out
    assert filename.read_text(encoding="utf-8") == "{broken"


def test_invalid_schema_rejected(tmp_path) -> None:
    store_sample(tmp_path)
    records = load_json(tmp_path / "cars.json")
    records[0]["id"] = True
    save_json(tmp_path / "cars.json", records)
    with pytest.raises(ValueError):
        load_data(tmp_path)


def test_write_error_keeps_memory_and_file(tmp_path, monkeypatch) -> None:
    _, _, trips = store_sample(tmp_path)
    filename = tmp_path / "trips.json"
    original = trips[0]
    old_contents = filename.read_bytes()

    def reject_replace(*args):
        raise PermissionError("Запись запрещена")

    monkeypatch.setattr(Path, "replace", reject_replace)
    monkeypatch.setattr("builtins.input", lambda _: "1")
    with pytest.raises(PermissionError):
        cancel_saved_trip(trips, tmp_path)
    assert trips[0] is original and not original.is_cancelled
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
    store_sample(tmp_path)
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
    cars, drivers, trips = load_data(tmp_path)
    assert len(cars) == len(drivers) == 4
    assert len(trips) == 2 and trips[-1].is_cancelled
    assert trips[-1].car is cars[-1] and trips[-1].driver is drivers[-1]
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
    store_sample(tmp_path)
    records = load_json(tmp_path / "trips.json")
    records[0]["car_id"] = 999
    save_json(tmp_path / "trips.json", records)
    with pytest.raises(KeyError):
        load_data(tmp_path)


def test_duplicate_ids_rejected(tmp_path) -> None:
    store_sample(tmp_path)
    records = load_json(tmp_path / "cars.json")
    save_json(tmp_path / "cars.json", [records[0], records[0]])
    with pytest.raises(ValueError, match="Повтор ID"):
        load_data(tmp_path)


def test_car_creation_and_capacity() -> None:
    car = Car(1, "Test", "А111АА77", 4, 48000, 40000, 10000, 8.5)
    assert car.id == 1 and car.model == "Test" and car.capacity == 4
    assert car.is_suitable_for(4) and not car.is_suitable_for(5)
    assert isinstance(car.maintenance, Maintenance)
    assert "А111АА77" in str(car)
    with pytest.raises(ValueError):
        Car.validate_capacity(0)


def test_maintenance_state_and_status() -> None:
    maintenance = Maintenance(40000, 10000)
    assert maintenance.remaining(48000) == 2000
    assert maintenance.remaining(48000, 120) == 1880
    assert "40000" in str(maintenance)
    assert "Требуется" in maintenance.get_status(50000, 120)
    assert "порога ТО" in maintenance.get_status(48000, 2000)
    with pytest.raises(ValueError):
        maintenance.remaining(39000)


def test_car_factory(tmp_path) -> None:
    cars, _, _ = store_sample(tmp_path)
    car = Car.from_data(load_json(tmp_path / "cars.json")[0])
    assert car.id == cars[0].id and car.plate == cars[0].plate
    assert car.maintenance.last_mileage == 40000


def test_trip_creation_links_and_string() -> None:
    cars, drivers, _ = sample_data()
    trip = Trip(7, cars[0], drivers[0], "2026-11-11", 120, 2)
    assert trip.car is cars[0] and trip.driver is drivers[0]
    assert trip.id == 7 and trip.trip_date == "2026-11-11"
    assert trip.calculate_fuel() == pytest.approx(10.2)
    assert "активна" in str(trip)
    trip.cancel()
    assert trip.is_cancelled and "отменена" in str(trip)


def test_cancel_retains_history_and_allows_new_trip() -> None:
    cars, drivers, trips = sample_data()
    old = trips[0]
    assert cancel_trip(trips, old.id) is old
    assert trips[0] is old and old.is_cancelled
    assert is_car_available(trips, old.car, old.trip_date)
    assert is_driver_available(trips, old.driver, old.trip_date)
    assert reserved_distance(trips, old.car) == 0
    new = create_trip(trips, old.car, old.driver, old.trip_date, 90, 8)
    assert new is not None and new.id != old.id
    assert new.car is old.car and new.driver is old.driver
    assert len(trips) == 2


def test_legacy_json_without_cancel_flag(tmp_path) -> None:
    store_sample(tmp_path)
    records = load_json(tmp_path / "trips.json")
    records[0].pop("is_cancelled")
    save_json(tmp_path / "trips.json", records)
    cars, drivers, trips = load_data(tmp_path)
    assert not trips[0].is_cancelled
    assert trips[0].car is cars[1] and trips[0].driver is drivers[1]


def test_json_stores_only_ids_for_relations(tmp_path) -> None:
    store_sample(tmp_path)
    record = load_json(tmp_path / "trips.json")[0]
    assert record["car_id"] == 2 and record["driver_id"] == 2
    assert record["is_cancelled"] is False
    assert "car" not in record and "driver" not in record


def test_cancelled_history_does_not_fail_active_validation(tmp_path) -> None:
    cars, drivers, trips = store_sample(tmp_path)
    trips[0].cancel()
    new = create_trip(trips, cars[1], drivers[1], "2026-11-10", 90, 8)
    assert new is not None
    save_trips(tmp_path / "trips.json", trips)
    _, _, restored = load_data(tmp_path)
    assert restored[0].is_cancelled and not restored[1].is_cancelled
    assert restored[0].car is restored[1].car


def test_invalid_cancel_flag_rejected(tmp_path) -> None:
    store_sample(tmp_path)
    records = load_json(tmp_path / "trips.json")
    records[0]["is_cancelled"] = "false"
    save_json(tmp_path / "trips.json", records)
    with pytest.raises(ValueError):
        load_data(tmp_path)


def test_saved_cancel_keeps_original_references(tmp_path, monkeypatch) -> None:
    cars, drivers, trips = store_sample(tmp_path)
    original = trips[0]
    monkeypatch.setattr("builtins.input", lambda _: "1")
    cancel_saved_trip(trips, tmp_path)
    assert trips[0] is original and original.is_cancelled
    assert original.car is cars[1] and original.driver is drivers[1]
    assert load_data(tmp_path)[2][0].is_cancelled


def test_menu_forbidden_trip_does_not_change_file(
        tmp_path, monkeypatch, capsys) -> None:
    store_sample(tmp_path)
    filename = tmp_path / "trips.json"
    original = filename.read_bytes()
    answers = iter(["11", "2", "2", "2026-11-10", "90", "8", "0"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    main(tmp_path)
    assert "автомобиль уже занят" in capsys.readouterr().out
    assert filename.read_bytes() == original


def test_add_car_write_failure_preserves_collection(
        tmp_path, monkeypatch) -> None:
    cars, drivers, trips = store_sample(tmp_path)
    original = list(cars)
    answers = iter(["Test", "С111СС77", "4", "100", "0", "10000", "7"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    def reject_replace(*args):
        raise PermissionError("Запись запрещена")

    monkeypatch.setattr(Path, "replace", reject_replace)
    with pytest.raises(PermissionError):
        handle_action("2", cars, drivers, trips, tmp_path)
    assert cars == original


def test_car_constructor_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        Car(1, "Test", "А111АА77", 0, 100, 0, 10000, 8.5)
    with pytest.raises(ValueError):
        Car(1, "Test", "А111АА77", 4, 100, 200, 10000, 8.5)
    with pytest.raises(ValueError):
        Car(1, "Test", "А111АА77", 4, 100, 0, 10000, float("nan"))


def test_trip_rejects_primitive_links() -> None:
    _, drivers, _ = sample_data()
    with pytest.raises(TypeError):
        Trip(1, {"id": 1}, drivers[0], "2026-11-11", 120, 2)


def test_cancelled_history_with_revoked_permission(tmp_path) -> None:
    cars, drivers, trips = store_sample(tmp_path)
    trips[0].cancel()
    drivers[1].has_permission = False
    save_trips(tmp_path / "trips.json", trips)
    save_drivers(tmp_path / "drivers.json", drivers)
    _, restored_drivers, restored = load_data(tmp_path)
    assert restored[0].is_cancelled
    assert restored[0].driver is restored_drivers[1]
    assert not restored[0].driver.can_drive()
