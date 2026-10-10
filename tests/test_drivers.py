"""Проверки объектов водителей и фабричного метода класса."""

import pytest

from models import Driver
from models.drivers import add_driver, find_driver_by_id


def test_driver_creation() -> None:
    driver = Driver(1, "Иванов Иван", True)
    assert driver.id == 1 and driver.name == "Иванов Иван"
    assert driver.has_permission and driver.can_drive()


def test_driver_string() -> None:
    driver = Driver(1, "Иванов Иван", True)
    assert "Иванов Иван" in str(driver) and "допуск: есть" in str(driver)


def test_driver_factory() -> None:
    driver = Driver.from_data(dict(id=2, name="Петров Петр",
                                   has_permission=False))
    assert isinstance(driver, Driver) and driver.id == 2
    assert not driver.can_drive()
    assert "не допущен" in driver.get_driver_status(False)


def test_driver_busy_status() -> None:
    driver = Driver(1, "Иванов Иван", True)
    assert "занят" in driver.get_driver_status(True)
    assert "доступен" in driver.get_driver_status(False)


def test_driver_add_and_find() -> None:
    drivers = []
    driver = add_driver(drivers, "Иванов Иван", True)
    assert drivers[0] is driver and find_driver_by_id(drivers, 1) is driver
    with pytest.raises(KeyError):
        find_driver_by_id(drivers, 999)


def test_invalid_driver_permission() -> None:
    with pytest.raises(ValueError):
        Driver(1, "Иванов Иван", "да")
