"""Консольное меню для работы с объектами автомобилей, водителей и поездок."""

from copy import copy
from pathlib import Path

from models import Car, Driver, Trip
from models.cars import (
    add_car, check_car_capacity, filter_cars_by_capacity, find_car_by_id,
    find_cars, sort_cars,
)
from models.drivers import add_driver, find_driver_by_id
from models.trips import (
    ALLOWED, cancel_trip, check_trip, create_trip, find_trip_by_id,
    is_car_available, is_driver_available, reserved_distance,
)
from storage import load_data, save_cars, save_drivers, save_trips
from utils import input_date, input_int, input_number, input_permission

DATA_DIR = Path(__file__).resolve().parent / "data"
MENU = """
=== Сервис учета автомобилей организации ===
1. Показать автомобили
2. Добавить автомобиль
3. Найти автомобиль по модели или госномеру
4. Проверить пассажирскую вместимость
5. Отобрать автомобили по вместимости
6. Отсортировать автомобили по вместимости
7. Показать водителей
8. Добавить водителя
9. Проверить доступность автомобиля и водителя на дату
10. Проверить подготовку поездки
11. Создать поездку
12. Отменить поездку
13. Показать поездки
0. Выход
"""


def show_cars(cars: list[Car]) -> None:
    """Вывести автомобили через их строковое представление."""
    if not cars:
        print("Автомобили не найдены.")
    for car in cars:
        print(car)


def show_drivers(drivers: list[Driver]) -> None:
    """Вывести объекты водителей через __str__."""
    if not drivers:
        print("Водителей пока нет.")
    for driver in drivers:
        print(driver)


def show_trips(trips: list[Trip]) -> None:
    """Показать участников поездок и состояние, включая отмененные записи."""
    if not trips:
        print("Поездок пока нет.")
    for trip in trips:
        print(trip)


def input_assignment(cars: list[Car],
                     drivers: list[Driver]) -> tuple[Car, Driver, str]:
    """Выбрать существующие объекты участников и запросить дату."""
    car = find_car_by_id(cars, input_int("ID автомобиля: "))
    driver = find_driver_by_id(drivers, input_int("ID водителя: "))
    return car, driver, input_date("Дата (ГГГГ-ММ-ДД): ")


def input_trip(cars: list[Car], drivers: list[Driver]
               ) -> tuple[Car, Driver, str, int, int]:
    """Запросить объекты участников и параметры полного маршрута."""
    car, driver, trip_date = input_assignment(cars, drivers)
    distance = input_int("Расстояние полного маршрута, км: ")
    passengers = input_int("Количество пассажиров без водителя: ")
    return car, driver, trip_date, distance, passengers


def show_trip_preview(trips: list[Trip], car: Car, driver: Driver,
                      trip_date: str, distance: int, passengers: int) -> None:
    """Сохраненный сценарий ПР1: подготовка поездки без ее создания."""
    reserved = reserved_distance(trips, car)
    print(f"Автомобиль: {car.model}, {car.plate}")
    print(f"Водитель: {driver.name}; дата: {trip_date}")
    print(car.get_service_status(distance, reserved))
    print(driver.get_driver_status(
        not is_driver_available(trips, driver, trip_date),
    ))
    status = check_trip(trips, car, driver, trip_date, distance, passengers)
    print(status)
    fuel = car.calculate_fuel(distance)
    print(f"Плановая потребность в топливе: {fuel:.1f} л")
    if status == ALLOWED:
        projected = car.mileage + reserved + distance
        remaining = car.service_remaining(reserved + distance)
        print(f"Пробег после всех поездок (прогноз): {projected} км")
        print(f"До ТО после всех поездок (прогноз): {remaining} км")


def create_new_trip(cars: list[Car], drivers: list[Driver],
                    trips: list[Trip], directory: Path) -> None:
    """Создать поездку через функцию и сохранить до изменения списка."""
    arguments = input_trip(cars, drivers)
    candidate = list(trips)
    trip = create_trip(candidate, *arguments)
    if trip is None:
        print(check_trip(trips, *arguments))
        return
    save_trips(directory / "trips.json", candidate)
    trips[:] = candidate
    print(f"Поездка создана, ID: {trip.id}.")


def cancel_saved_trip(trips: list[Trip], directory: Path) -> None:
    """Сохранить отмену, затем изменить состояние исходного объекта."""
    trip_id = input_int("ID поездки для отмены: ")
    original = find_trip_by_id(trips, trip_id)
    candidate = [copy(trip) if trip is original else trip for trip in trips]
    cancel_trip(candidate, trip_id)
    save_trips(directory / "trips.json", candidate)
    original.cancel()
    print("Поездка отменена.")


def handle_action(choice: str, cars: list[Car], drivers: list[Driver],
                  trips: list[Trip], directory: Path) -> None:
    """Выполнить пункт меню с коллекциями объектов и безопасным сохранением."""
    if choice == "1":
        show_cars(cars)
    elif choice == "2":
        candidate = list(cars)
        car = add_car(
            candidate, input("Модель: "), input("Госномер: "),
            input_int("Пассажирских мест без водителя: "),
            input_int("Текущий пробег, км: ", 0),
            input_int("Пробег последнего ТО, км: ", 0),
            input_int("Интервал ТО, км: "),
            input_number("Расход на 100 км, л: "),
        )
        save_cars(directory / "cars.json", candidate)
        cars[:] = candidate
        print(f"Автомобиль добавлен, ID: {car.id}.")
    elif choice == "3":
        show_cars(find_cars(cars, input("Модель или госномер: ")))
    elif choice == "4":
        result = check_car_capacity(cars, input_int("ID автомобиля: "),
                                    input_int("Количество пассажиров: "))
        print("Мест достаточно." if result else "Мест недостаточно.")
    elif choice == "5":
        show_cars(filter_cars_by_capacity(
            cars, input_int("Минимум пассажирских мест: "),
        ))
    elif choice == "6":
        show_cars(sort_cars(cars))
    elif choice == "7":
        show_drivers(drivers)
    elif choice == "8":
        candidate = list(drivers)
        driver = add_driver(candidate, input("ФИО водителя: "),
                            input_permission("Допуск есть (да/нет): "))
        save_drivers(directory / "drivers.json", candidate)
        drivers[:] = candidate
        print(f"Водитель добавлен, ID: {driver.id}.")
    elif choice == "9":
        car, driver, trip_date = input_assignment(cars, drivers)
        car_free = is_car_available(trips, car, trip_date)
        driver_free = is_driver_available(trips, driver, trip_date)
        print("Автомобиль свободен." if car_free else "Автомобиль занят.")
        print("Водитель свободен." if driver_free else "Водитель занят.")
    elif choice == "10":
        show_trip_preview(trips, *input_trip(cars, drivers))
    elif choice == "11":
        create_new_trip(cars, drivers, trips, directory)
    elif choice == "12":
        cancel_saved_trip(trips, directory)
    elif choice == "13":
        show_trips(trips)
    else:
        print("Неизвестный пункт меню. Выберите число от 0 до 13.")


def main(directory: Path = DATA_DIR) -> None:
    """Загрузить объекты и выполнять прежнее меню с обработкой ошибок."""
    try:
        cars, drivers, trips = load_data(directory)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Не удалось загрузить данные: {error}")
        print("Исправьте файлы JSON и повторите запуск; они не перезаписаны.")
        return
    try:
        while True:
            print(MENU)
            choice = input("Выберите действие: ").strip()
            if choice == "0":
                print("Работа завершена.")
                break
            try:
                handle_action(choice, cars, drivers, trips, directory)
            except KeyError as error:
                print(f"Запись с ID {error.args[0]} не найдена.")
            except (ValueError, OSError) as error:
                print(f"Ошибка: {error}")
    except (EOFError, KeyboardInterrupt):
        print("\nРабота завершена. Все ранее сохраненные изменения доступны.")


if __name__ == "__main__":
    main()
