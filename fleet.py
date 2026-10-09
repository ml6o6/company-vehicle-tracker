from utils import require_int, require_number, require_text

#Автомобили, водители и контроль обслуживания автопарка

def validate_car(car: dict) -> None:
    #Проверка обязательных полей словаря автомобиля."""
    require_int(car["id"], "ID автомобиля", 1)
    require_text(car["model"], "Модель")
    require_text(car["plate"], "Госномер")
    require_int(car["capacity"], "Пассажирские места", 1)
    require_int(car["mileage"], "Пробег")
    require_int(car["last_service_mileage"], "Пробег последнего ТО")
    require_int(car["service_interval"], "Интервал ТО", 1)
    require_number(car["fuel_consumption"], "Расход топлива")
    if car["last_service_mileage"] > car["mileage"]:
        raise ValueError("Пробег последнего ТО превышает текущий пробег.")


def validate_driver(driver: dict) -> None:
    #Проверка обязательных полей словаря водителя
    require_int(driver["id"], "ID водителя", 1)
    require_text(driver["name"], "ФИО водителя")
    if type(driver["has_permission"]) is not bool:
        raise ValueError("Допуск водителя должен быть логическим значением.")


def add_car(cars: dict[int, dict], model: str, plate: str, capacity: int,
            mileage: int, last_service_mileage: int, service_interval: int,
            fuel_consumption: float) -> dict:
    #Добавить автомобиль с уникальным госномером; вернуть словарь.
    car = dict(id=max(cars, default=0) + 1,
               model=require_text(model, "Модель"),
               plate=require_text(plate, "Госномер").upper(),
               capacity=capacity,
               mileage=mileage, last_service_mileage=last_service_mileage,
               service_interval=service_interval,
               fuel_consumption=fuel_consumption)
    validate_car(car)
    if any(item["plate"].casefold() == car["plate"].casefold()
           for item in cars.values()):
        raise ValueError("Автомобиль с таким госномером уже существует.")
    cars[car["id"]] = car
    return car


def add_driver(drivers: dict[int, dict], name: str,
               has_permission: bool) -> dict:
    #Добавить водителя с новым ID; вернуть его словарь.
    driver = dict(id=max(drivers, default=0) + 1,
                  name=require_text(name, "ФИО"),
                  has_permission=has_permission)
    validate_driver(driver)
    drivers[driver["id"]] = driver
    return driver


def find_cars(cars: dict[int, dict], query: str) -> list[dict]:
    #Найти по подстроке модели или госномера без учета регистра.
    query = require_text(query, "Поисковый запрос").casefold()
    return [car for car in cars.values()
            if query in car["model"].casefold()
            or query in car["plate"].casefold()]


def check_car_capacity(cars: dict[int, dict], car_id: int,
                       passengers: int) -> bool:
    #Проверить вместимость; неизвестный ID дает KeyError.
    require_int(passengers, "Пассажиры", 1)
    return cars[car_id]["capacity"] >= passengers


def filter_cars_by_capacity(cars: dict[int, dict],
                            passengers: int) -> list[dict]:
    #Отобрать подходящие автомобили через генератор и вернуть список.
    require_int(passengers, "Пассажиры", 1)
    suitable = (car for car in cars.values() if car["capacity"] >= passengers)
    return list(suitable)


def sort_cars(cars: dict[int, dict]) -> list[dict]:
    #Вернуть автомобили по возрастанию вместимости, затем по ID.
    return sorted(cars.values(), key=lambda car: (car["capacity"], car["id"]))


def service_remaining(mileage: int, last_service_mileage: int,
                      service_interval: int) -> int:
    #Проверить пробеги и вернуть расстояние до ТО, включая просрочку.
    require_int(mileage, "Пробег")
    require_int(last_service_mileage, "Пробег последнего ТО")
    require_int(service_interval, "Интервал ТО", 1)
    if last_service_mileage > mileage:
        raise ValueError("Пробег последнего ТО превышает текущий пробег.")
    return last_service_mileage + service_interval - mileage


def get_service_status(mileage: int, last_service_mileage: int,
                       service_interval: int, trip_distance: float) -> str:
    #вернуть статус ТО до выезда и на конец маршрута.
    try:
        require_number(trip_distance, "Расстояние")
        remaining = service_remaining(
            mileage, last_service_mileage, service_interval,
        )
    except ValueError:
        return "Ошибка: некорректные данные пробега или интервала ТО."
    if remaining <= 0:
        return "Требуется обслуживание до выезда."
    if trip_distance >= remaining:
        message = "Поездка достигнет порога ТО: "
        return message + "обслуживание нужно до выезда."
    return f"Обслуживание не требуется. До ТО: {remaining} км."


def get_driver_status(driver_has_permission: bool,
                      driver_is_busy: bool) -> str:
    # вернуть статус допуска и занятости водителя.
    if not driver_has_permission:
        return "Водитель не допущен к управлению этим автомобилем."
    if driver_is_busy:
        return "Водитель уже занят в другой поездке."
    return "Водитель доступен для поездки."
