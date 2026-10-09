#Планирование, проверка доступности и отмена поездок.

from fleet import check_car_capacity, service_remaining
from utils import require_int, require_number, validate_date

ALLOWED = "Поездка разрешена."

# Свободен ли автомобиль на дату; одна поездка занимает весь день.
def is_car_available(trips: list[dict], car_id: int, trip_date: str) -> bool:
    validate_date(trip_date)
    for trip in trips:
        if trip["car_id"] == car_id and trip["trip_date"] == trip_date:
            return False
    return True

# Свободен ли водитель на дату во всем автопарке.
def is_driver_available(trips: list[dict], driver_id: int,
                        trip_date: str) -> bool:
    validate_date(trip_date)
    for trip in trips:
        if trip["driver_id"] == driver_id and trip["trip_date"] == trip_date:
            return False
    return True

#   Сумма маршрутов всех сохраненных поездок автомобиля до следующего ТО.
def reserved_distance(trips: list[dict], car_id: int) -> float:
    return sum(trip["distance"] for trip in trips if trip["car_id"] == car_id)

# вернуть решение и первую причину запрета выезда.
def get_trip_status(car_is_busy: bool, driver_has_permission: bool,
                    driver_is_busy: bool, mileage: int,
                    last_service_mileage: int, service_interval: int,
                    trip_distance: float) -> str:
    try:
        remaining = service_remaining(
            mileage, last_service_mileage, service_interval,
        )
        require_number(trip_distance, "Расстояние")
    except ValueError:
        return "Поездка запрещена: некорректные исходные данные."
    if car_is_busy:
        return "Поездка запрещена: автомобиль уже занят."
    if not driver_has_permission or driver_is_busy:
        return "Поездка запрещена: водитель недоступен."
    if remaining <= 0:
        return "Поездка запрещена: требуется обслуживание."
    if trip_distance >= remaining:
        return "Поездка запрещена: маршрут достигнет порога ТО."
    return ALLOWED

# литры топлива без округления; -1.0 при неверных данных.
def calculate_fuel(trip_distance: float, fuel_consumption: float) -> float:
    try:
        require_number(trip_distance, "Расстояние")
        require_number(fuel_consumption, "Расход")
    except ValueError:
        return -1.0
    return trip_distance * fuel_consumption / 100

# Проверить данные и готовность к поездке без изменения коллекций.
def check_trip(cars: dict[int, dict], drivers: dict[int, dict],
               trips: list[dict], car_id: int, driver_id: int,
               trip_date: str, distance: int, passengers: int) -> str:
    require_int(car_id, "ID автомобиля", 1)
    require_int(driver_id, "ID водителя", 1)
    require_int(distance, "Расстояние", 1)
    validate_date(trip_date)
    car, driver = cars[car_id], drivers[driver_id]
    if not check_car_capacity(cars, car_id, passengers):
        return "Поездка запрещена: недостаточно пассажирских мест."
    return get_trip_status(
        not is_car_available(trips, car_id, trip_date),
        driver["has_permission"],
        not is_driver_available(trips, driver_id, trip_date),
        car["mileage"] + reserved_distance(trips, car_id),
        car["last_service_mileage"], car["service_interval"], distance,
    )

# Создать поездку с новым ID; при запрете бросить ValueError.
def create_trip(cars: dict[int, dict], drivers: dict[int, dict],
                trips: list[dict], car_id: int, driver_id: int,
                trip_date: str, distance: int, passengers: int) -> dict:
    status = check_trip(cars, drivers, trips, car_id, driver_id,
                        trip_date, distance, passengers)
    if status != ALLOWED:
        raise ValueError(status)
    trip = dict(id=max((item["id"] for item in trips), default=0) + 1,
                car_id=car_id, driver_id=driver_id, trip_date=trip_date,
                distance=distance, passengers=passengers)
    trips.append(trip)
    return trip

# Удалить поездку по ID и вернуть ее; неизвестный ID дает KeyError.
def cancel_trip(trips: list[dict], trip_id: int) -> dict:
    require_int(trip_id, "ID поездки", 1)
    for index, trip in enumerate(trips):
        if trip["id"] == trip_id:
            return trips.pop(index)
    raise KeyError(trip_id)
