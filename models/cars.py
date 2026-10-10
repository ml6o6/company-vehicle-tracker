"""Автомобиль и операции над коллекцией автомобилей."""

from __future__ import annotations

from utils import require_int, require_number, require_text
from .maintenance import Maintenance


class Car:
    """Служебный автомобиль с пассажирскими местами и данными ТО."""

    def __init__(self, car_id: int, model: str, plate: str, capacity: int,
                 mileage: int, last_service_mileage: int,
                 service_interval: int, fuel_consumption: float) -> None:
        self.id = require_int(car_id, "ID автомобиля", 1)
        self.model = require_text(model, "Модель")
        self.plate = require_text(plate, "Госномер").upper()
        self.validate_capacity(capacity)
        self.capacity = capacity
        self.mileage = require_int(mileage, "Пробег")
        self.fuel_consumption = require_number(fuel_consumption, "Расход")
        self.maintenance = Maintenance(last_service_mileage, service_interval)
        self.maintenance.remaining(self.mileage)

    @staticmethod
    def validate_capacity(capacity: int) -> None:
        """Проверить вместимость независимо от экземпляра автомобиля."""
        require_int(capacity, "Пассажирские места", 1)

    @classmethod
    def from_data(cls, data: dict) -> Car:
        """Восстановить автомобиль из записи JSON формата ПР2."""
        return cls(data["id"], data["model"], data["plate"], data["capacity"],
                   data["mileage"], data["last_service_mileage"],
                   data["service_interval"], data["fuel_consumption"])

    def is_suitable_for(self, passengers: int) -> bool:
        """Проверить число пассажиров, не включая водителя."""
        require_int(passengers, "Пассажиры", 1)
        return self.capacity >= passengers

    def service_remaining(self, reserved: int = 0) -> int:
        """Получить остаток пробега у связанного объекта обслуживания."""
        return self.maintenance.remaining(self.mileage, reserved)

    def get_service_status(self, distance: int, reserved: int = 0) -> str:
        """Сохраненный сценарий ПР1: вернуть статус ТО для маршрута."""
        return self.maintenance.get_status(self.mileage, distance, reserved)

    def calculate_fuel(self, distance: float) -> float:
        """Рассчитать литры топлива для полного маршрута."""
        require_number(distance, "Расстояние")
        return distance * self.fuel_consumption / 100

    def __str__(self) -> str:
        return (f"{self.id}: {self.model} | {self.plate} | "
                f"мест: {self.capacity} | пробег: {self.mileage} км")


def find_car_by_id(cars: list[Car], car_id: int) -> Car:
    """Найти объект по ID; для неизвестного ID вызвать KeyError."""
    require_int(car_id, "ID автомобиля", 1)
    for car in cars:
        if car.id == car_id:
            return car
    raise KeyError(car_id)


def add_car(cars: list[Car], model: str, plate: str, capacity: int,
            mileage: int, last_service_mileage: int, service_interval: int,
            fuel_consumption: float) -> Car:
    """Создать автомобиль, проверить уникальность госномера и добавить."""
    car = Car(max((item.id for item in cars), default=0) + 1,
              model, plate, capacity, mileage, last_service_mileage,
              service_interval, fuel_consumption)
    if any(item.plate.casefold() == car.plate.casefold() for item in cars):
        raise ValueError("Автомобиль с таким госномером уже существует.")
    cars.append(car)
    return car


def find_cars(cars: list[Car], query: str) -> list[Car]:
    """Искать объекты по подстроке модели или госномера."""
    query = require_text(query, "Поисковый запрос").casefold()
    return [car for car in cars if query in car.model.casefold()
            or query in car.plate.casefold()]


def check_car_capacity(cars: list[Car], car_id: int, passengers: int) -> bool:
    """Найти автомобиль и вызвать его метод проверки вместимости."""
    return find_car_by_id(cars, car_id).is_suitable_for(passengers)


def filter_cars_by_capacity(cars: list[Car], passengers: int) -> list[Car]:
    """Отобрать объекты по вместимости, используя метод автомобиля."""
    require_int(passengers, "Пассажиры", 1)
    return [car for car in cars if car.is_suitable_for(passengers)]


def sort_cars(cars: list[Car]) -> list[Car]:
    """Вернуть новый список по вместимости, затем по ID."""
    return sorted(cars, key=lambda car: (car.capacity, car.id))
