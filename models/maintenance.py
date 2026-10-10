"""Данные последнего технического обслуживания автомобиля."""

from utils import require_int, require_number


class Maintenance:
    """Пробег последнего ТО и установленный межсервисный интервал."""

    def __init__(self, last_mileage: int, interval: int) -> None:
        self.last_mileage = require_int(last_mileage, "Пробег последнего ТО")
        self.interval = require_int(interval, "Интервал ТО", 1)

    def remaining(self, mileage: int, reserved: int = 0) -> int:
        """Вернуть остаток до ТО с учетом запланированного пробега."""
        require_int(mileage, "Пробег")
        require_int(reserved, "Запланированный пробег")
        if self.last_mileage > mileage:
            raise ValueError("Пробег последнего ТО превышает текущий пробег.")
        return self.last_mileage + self.interval - mileage - reserved

    def get_status(self, mileage: int, distance: int,
                   reserved: int = 0) -> str:
        """Проверить срок обслуживания перед полным маршрутом."""
        require_number(distance, "Расстояние")
        remaining = self.remaining(mileage, reserved)
        if remaining <= 0:
            return "Требуется обслуживание до выезда."
        if distance >= remaining:
            return ("Поездка достигнет порога ТО: "
                    "обслуживание нужно до выезда.")
        return f"Обслуживание не требуется. До ТО: {remaining} км."

    def __str__(self) -> str:
        return (f"Последнее ТО: {self.last_mileage} км; "
                f"интервал: {self.interval} км")
