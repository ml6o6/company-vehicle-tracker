#Консольный интерфейс сервиса учета автомобилей организации.

from copy import deepcopy
from pathlib import Path

from fleet import (
    add_car, add_driver, check_car_capacity, filter_cars_by_capacity,
    find_cars,
    get_driver_status, get_service_status, sort_cars,
)
from storage import load_data, save_change
from trips import (
    ALLOWED, calculate_fuel, cancel_trip, check_trip, create_trip,
    is_car_available, is_driver_available, reserved_distance,
)
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


def show_cars(cars: list[dict]) -> None:
    #Вывести ID, модель, госномер, вместимость и пробег автомобилей.
    if not cars:
        print("Автомобили не найдены.")
    for car in cars:
        print(f"{car['id']}: {car['model']} | {car['plate']} | "
              f"мест: {car['capacity']} | пробег: {car['mileage']} км")


def show_drivers(drivers: dict[int, dict]) -> None:
    #Вывести список водителей и наличие общего допуска к автопарку.
    if not drivers:
        print("Водителей пока нет.")
    for driver in drivers.values():
        permission = "есть" if driver["has_permission"] else "нет"
        print(f"{driver['id']}: {driver['name']} | допуск: {permission}")


def show_trips(data: dict) -> None:
    #Вывести поездки, участников и расчет топлива.
    if not data["trips"]:
        print("Поездок пока нет.")
    for trip in data["trips"]:
        car = data["cars"][trip["car_id"]]
        driver = data["drivers"][trip["driver_id"]]
        fuel = calculate_fuel(trip["distance"], car["fuel_consumption"])
        print(f"{trip['id']}: {trip['trip_date']} | {car['plate']} | "
              f"{driver['name']} | {trip['distance']} км | "
              f"пассажиров: {trip['passengers']} | топливо: {fuel:.1f} л")


def input_assignment(data: dict) -> tuple[int, int, str]:
    #Запросить существующие автомобиль, водителя и календарную дату.
    car_id = input_int("ID автомобиля: ")
    driver_id = input_int("ID водителя: ")
    data["cars"][car_id]
    data["drivers"][driver_id]
    return car_id, driver_id, input_date("Дата (ГГГГ-ММ-ДД): ")


def input_trip(data: dict) -> tuple[int, int, str, int, int]:
    #Запросить участников, дату, полный маршрут и число пассажиров.
    car_id, driver_id, trip_date = input_assignment(data)
    distance = input_int("Расстояние полного маршрута, км: ")
    passengers = input_int("Количество пассажиров без водителя: ")
    return car_id, driver_id, trip_date, distance, passengers


def show_trip_preview(data: dict, car_id: int, driver_id: int,
                      trip_date: str, distance: int, passengers: int) -> None:
    #вывести ТО, статус водителя, решение и расчет топлива.
    car, driver = data["cars"][car_id], data["drivers"][driver_id]
    mileage = car["mileage"] + reserved_distance(data["trips"], car_id)
    print(f"Автомобиль: {car['model']}, {car['plate']}")
    print(f"Водитель: {driver['name']}; дата: {trip_date}")
    print(get_service_status(mileage, car["last_service_mileage"],
                             car["service_interval"], distance))
    print(get_driver_status(
        driver["has_permission"],
        not is_driver_available(data["trips"], driver_id, trip_date),
    ))
    status = check_trip(data["cars"], data["drivers"], data["trips"],
                        car_id, driver_id, trip_date, distance, passengers)
    print(status)
    fuel = calculate_fuel(distance, car["fuel_consumption"])
    print(f"Плановая потребность в топливе: {fuel:.1f} л")
    if status == ALLOWED:
        remaining = (car["last_service_mileage"] + car["service_interval"]
                     - mileage - distance)
        print(f"Пробег после всех поездок (прогноз): {mileage + distance} км")
        print(f"До ТО после всех поездок (прогноз): {remaining} км")


def handle_action(choice: str, data: dict, directory: Path) -> None:
    #Выполнить пункт меню; сохранять изменения перед заменой в памяти.
    cars, drivers, trips = data["cars"], data["drivers"], data["trips"]
    if choice == "1":
        show_cars(list(cars.values()))
    elif choice == "2":
        candidate = deepcopy(cars)
        car = add_car(
            candidate, input("Модель: "), input("Госномер: "),
            input_int("Пассажирских мест без водителя: "),
            input_int("Текущий пробег, км: ", 0),
            input_int("Пробег последнего ТО, км: ", 0),
            input_int("Интервал ТО, км: "),
            input_number("Расход на 100 км, л: "),
        )
        save_change(directory, data, "cars", candidate)
        print(f"Автомобиль добавлен, ID: {car['id']}.")
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
        candidate = deepcopy(drivers)
        driver = add_driver(candidate, input("ФИО водителя: "),
                            input_permission("Допуск есть (да/нет): "))
        save_change(directory, data, "drivers", candidate)
        print(f"Водитель добавлен, ID: {driver['id']}.")
    elif choice == "9":
        car_id, driver_id, trip_date = input_assignment(data)
        car_free = is_car_available(trips, car_id, trip_date)
        driver_free = is_driver_available(trips, driver_id, trip_date)
        print("Автомобиль свободен." if car_free else "Автомобиль занят.")
        print("Водитель свободен." if driver_free else "Водитель занят.")
    elif choice == "10":
        show_trip_preview(data, *input_trip(data))
    elif choice == "11":
        candidate = deepcopy(trips)
        trip = create_trip(cars, drivers, candidate, *input_trip(data))
        save_change(directory, data, "trips", candidate)
        print(f"Поездка создана, ID: {trip['id']}.")
    elif choice == "12":
        candidate = deepcopy(trips)
        cancel_trip(candidate, input_int("ID поездки для отмены: "))
        save_change(directory, data, "trips", candidate)
        print("Поездка отменена.")
    elif choice == "13":
        show_trips(data)
    else:
        print("Неизвестный пункт меню. Выберите число от 0 до 13.")


def main(directory: Path = DATA_DIR) -> None:
    #Загрузить JSON и выполнить меню с обработкой ввода и ошибок файлов.
    try:
        data = load_data(directory)
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
                handle_action(choice, data, directory)
            except KeyError as error:
                print(f"Запись с ID {error.args[0]} не найдена.")
            except (ValueError, OSError) as error:
                print(f"Ошибка: {error}")
    except (EOFError, KeyboardInterrupt):
        print("\nРабота завершена. Все ранее сохраненные изменения доступны.")


if __name__ == "__main__":
    main()
