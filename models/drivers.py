"""Водитель и операции над коллекцией водителей."""

from __future__ import annotations

from utils import require_int, require_text


class Driver:
    """Водитель с общим допуском к автомобилям организации."""

    def __init__(self, driver_id: int, name: str,
                 has_permission: bool) -> None:
        self.id = require_int(driver_id, "ID водителя", 1)
        self.name = require_text(name, "ФИО водителя")
        if type(has_permission) is not bool:
            raise ValueError("Допуск водителя должен быть логическим.")
        self.has_permission = has_permission

    @classmethod
    def from_data(cls, data: dict) -> Driver:
        """Создать водителя из записи JSON."""
        return cls(data["id"], data["name"], data["has_permission"])

    def can_drive(self) -> bool:
        """Проверить наличие допуска к автопарку."""
        return self.has_permission

    def get_driver_status(self, is_busy: bool) -> str:
        """Сохраненный сценарий ПР1: допуск и занятость водителя."""
        if not self.can_drive():
            return "Водитель не допущен к управлению этим автомобилем."
        if is_busy:
            return "Водитель уже занят в другой поездке."
        return "Водитель доступен для поездки."

    def __str__(self) -> str:
        permission = "есть" if self.can_drive() else "нет"
        return f"{self.id}: {self.name} | допуск: {permission}"


def find_driver_by_id(drivers: list[Driver], driver_id: int) -> Driver:
    """Найти водителя; неизвестный ID дает KeyError."""
    require_int(driver_id, "ID водителя", 1)
    for driver in drivers:
        if driver.id == driver_id:
            return driver
    raise KeyError(driver_id)


def add_driver(drivers: list[Driver], name: str,
               has_permission: bool) -> Driver:
    """Создать водителя с новым ID и добавить его в коллекцию."""
    driver = Driver(max((item.id for item in drivers), default=0) + 1,
                    name, has_permission)
    drivers.append(driver)
    return driver
