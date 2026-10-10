# Проверка значений и безопасный ввод данных из консоли.

from datetime import date
from math import isfinite


# Проверить целое значение и нижнюю границу; вернуть значение.
def require_int(value: int, name: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name}: требуется целое число от {minimum}.")
    return value


# Проверить положительное конечное число; вернуть значение.
def require_number(value: float, name: str) -> float:
    if (type(value) not in (int, float) or not isfinite(value)
            or value <= 0):
        raise ValueError(f"{name}: требуется положительное конечное число.")
    return value


# Убрать пробелы по краям непустой строки; вернуть строку.
def require_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}: требуется непустая строка.")
    return value.strip()


# Проверить календарную дату строго в формате ГГГГ-ММ-ДД.
def validate_date(value: str) -> str:
    if (not isinstance(value, str)
            or date.fromisoformat(value).isoformat() != value):
        raise ValueError("Дата должна иметь формат ГГГГ-ММ-ДД.")
    return value


# Запрашивать целое число до получения допустимого значения.
def input_int(prompt: str, minimum: int = 1) -> int:
    while True:
        try:
            return require_int(int(input(prompt)), "Значение", minimum)
        except ValueError as error:
            print(f"Ошибка ввода: {error}")


# Запрашивать положительное число; принимать точку или запятую.
def input_number(prompt: str) -> float:
    while True:
        try:
            value = float(input(prompt).replace(",", "."))
            return require_number(value, "Значение")
        except ValueError as error:
            print(f"Ошибка ввода: {error}")


# Запрашивать календарную дату до получения корректного значения.
def input_date(prompt: str) -> str:
    while True:
        try:
            return validate_date(input(prompt).strip())
        except ValueError:
            print("Ошибка: введите существующую дату в формате ГГГГ-ММ-ДД.")


# Прочитать логический допуск водителя, повторяя неверный ввод.
def input_permission(prompt: str) -> bool:
    while True:
        value = input(prompt).strip().casefold()
        if value in ("да", "yes", "1"):
            return True
        if value in ("нет", "no", "0"):
            return False
        print("Введите да или нет.")
