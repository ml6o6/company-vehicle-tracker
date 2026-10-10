"""Поездка и функции планирования с учетом активных поездок."""

from .cars import Car
from .drivers import Driver
from utils import require_int, validate_date

ALLOWED = "Поездка разрешена."


class Trip:
    """Поездка, связывающая существующие объекты автомобиля и водителя."""

    def __init__(self, trip_id: int, car: Car, driver: Driver,
                 trip_date: str, distance: int, passengers: int,
                 is_cancelled: bool = False) -> None:
        self.id = require_int(trip_id, "ID поездки", 1)
        if not isinstance(car, Car) or not isinstance(driver, Driver):
            raise TypeError("Поездка должна связывать Car и Driver.")
        if type(is_cancelled) is not bool:
            raise ValueError("Признак отмены должен быть логическим.")
        self.car = car
        self.driver = driver
        self.trip_date = validate_date(trip_date)
        self.distance = require_int(distance, "Расстояние", 1)
        self.passengers = require_int(passengers, "Пассажиры", 1)
        self.is_cancelled = is_cancelled

    def cancel(self) -> None:
        """Отменить поездку, сохранив объект и ссылки на участников."""
        self.is_cancelled = True

    def calculate_fuel(self) -> float:
        """Рассчитать топливо через связанный объект автомобиля."""
        return self.car.calculate_fuel(self.distance)

    def __str__(self) -> str:
        state = "отменена" if self.is_cancelled else "активна"
        return (f"{self.id}: {self.trip_date} | {self.car.model}, "
                f"{self.car.plate} | {self.driver.name} | "
                f"{self.distance} км | пассажиров: {self.passengers} | "
                f"топливо: {self.calculate_fuel():.1f} л | {state}")


def is_car_available(trips: list[Trip], car: Car, trip_date: str) -> bool:
    """Проверить занятость автомобиля активными поездками на дату."""
    validate_date(trip_date)
    for trip in trips:
        if (not trip.is_cancelled and trip.car.id == car.id
                and trip.trip_date == trip_date):
            return False
    return True


def is_driver_available(trips: list[Trip], driver: Driver,
                        trip_date: str) -> bool:
    """Проверить занятость водителя активными поездками на дату."""
    validate_date(trip_date)
    return not any(not trip.is_cancelled and trip.driver.id == driver.id
                   and trip.trip_date == trip_date for trip in trips)


def reserved_distance(trips: list[Trip], car: Car) -> int:
    """Суммировать пробег только активных поездок автомобиля."""
    return sum(trip.distance for trip in trips
               if trip.car.id == car.id and not trip.is_cancelled)


def check_trip(trips: list[Trip], car: Car, driver: Driver,
               trip_date: str, distance: int, passengers: int) -> str:
    """Проверить объекты и правила выезда без изменения коллекции."""
    validate_date(trip_date)
    require_int(distance, "Расстояние", 1)
    if not car.is_suitable_for(passengers):
        return "Поездка запрещена: недостаточно пассажирских мест."
    if not is_car_available(trips, car, trip_date):
        return "Поездка запрещена: автомобиль уже занят."
    if not driver.can_drive() or not is_driver_available(
            trips, driver, trip_date):
        return "Поездка запрещена: водитель недоступен."
    remaining = car.service_remaining(reserved_distance(trips, car))
    if remaining <= 0:
        return "Поездка запрещена: требуется обслуживание."
    if distance >= remaining:
        return "Поездка запрещена: маршрут достигнет порога ТО."
    return ALLOWED


def create_trip(trips: list[Trip], car: Car, driver: Driver,
                trip_date: str, distance: int, passengers: int) -> Trip | None:
    """Добавить связанную поездку; вернуть None, если выезд запрещен."""
    status = check_trip(trips, car, driver, trip_date, distance, passengers)
    if status != ALLOWED:
        return None
    trip = Trip(max((item.id for item in trips), default=0) + 1,
                car, driver, trip_date, distance, passengers)
    trips.append(trip)
    return trip


def find_trip_by_id(trips: list[Trip], trip_id: int) -> Trip:
    """Найти поездку по ID; неизвестный ID дает KeyError."""
    require_int(trip_id, "ID поездки", 1)
    for trip in trips:
        if trip.id == trip_id:
            return trip
    raise KeyError(trip_id)


def cancel_trip(trips: list[Trip], trip_id: int) -> Trip:
    """Найти поездку и вызвать cancel, не удаляя запись из истории."""
    trip = find_trip_by_id(trips, trip_id)
    trip.cancel()
    return trip
