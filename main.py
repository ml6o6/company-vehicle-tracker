# Проверка готовности служебного автомобиля к одной поездке

from datetime import date


def get_service_status(mileage, last_service_mileage, service_interval,
                       trip_distance):
    """Проверить срок ТО до выезда и на конец полного маршрута."""
    if (mileage < 0 or last_service_mileage < 0
            or last_service_mileage > mileage or service_interval <= 0
            or trip_distance <= 0):
        return "Ошибка: некорректные данные пробега или интервала ТО."
    remaining = last_service_mileage + service_interval - mileage
    if remaining <= 0:
        return "Требуется обслуживание до выезда."
    elif trip_distance >= remaining:
        return "Поездка достигнет порога ТО: обслуживание нужно до выезда."
    else:
        return f"Обслуживание не требуется. До ТО: {remaining} км."


def get_driver_status(driver_has_permission, driver_is_busy):
    """Проверить допуск к автомобилю и занятость водителя."""
    if not driver_has_permission:
        return "Водитель не допущен к управлению этим автомобилем."
    elif driver_is_busy:
        return "Водитель уже занят в другой поездке."
    else:
        return "Водитель доступен для поездки."


def get_trip_status(car_is_busy, driver_has_permission, driver_is_busy,
                    mileage, last_service_mileage, service_interval,
                    trip_distance):
    """Вернуть решение о выезде; первый запрет определяет причину."""
    if (mileage < 0 or last_service_mileage < 0
            or last_service_mileage > mileage or service_interval <= 0
            or trip_distance <= 0):
        return "Поездка запрещена: некорректные исходные данные."
    remaining = last_service_mileage + service_interval - mileage
    if car_is_busy:
        return "Поездка запрещена: автомобиль уже занят."
    elif not driver_has_permission or driver_is_busy:
        return "Поездка запрещена: водитель недоступен."
    elif remaining <= 0:
        return "Поездка запрещена: требуется обслуживание."
    elif trip_distance >= remaining:
        return "Поездка запрещена: маршрут достигнет порога ТО."
    else:
        return "Поездка разрешена."


def calculate_fuel(trip_distance, fuel_consumption):
    """Рассчитать литры без округления; -1.0 означает ошибку данных."""
    if trip_distance <= 0 or fuel_consumption <= 0:
        return -1.0
    return trip_distance * fuel_consumption / 100


def main():
    #Cценарий подготовки одной поездки
    car_model = "Lada Vesta"
    car_plate = "А123ВС77"
    driver_name = "Иванов Иван Иванович"
    trip_date = date.today()
    mileage = int("48000")
    last_service_mileage = 40000
    service_interval = 10000
    trip_distance = int("120")
    fuel_consumption = float("8.5")
    car_is_busy = False
    driver_has_permission = True
    driver_is_busy = False

    service_status = get_service_status(
        mileage, last_service_mileage, service_interval, trip_distance,
    )
    driver_status = get_driver_status(driver_has_permission, driver_is_busy)
    trip_status = get_trip_status(
        car_is_busy, driver_has_permission, driver_is_busy,
        mileage, last_service_mileage, service_interval, trip_distance,
    )
    fuel_required = calculate_fuel(trip_distance, fuel_consumption)

    print("СЕРВИС УЧЕТА АВТОМОБИЛЕЙ ОРГАНИЗАЦИИ")
    print(f"Дата поездки: {trip_date:%d.%m.%Y}")
    print(f"Автомобиль: {car_model}, госномер {car_plate}")
    print(f"Водитель: {driver_name}")
    print(f"Пробег: {mileage} км; последнее ТО: {last_service_mileage} км")
    print(f"Интервал ТО: {service_interval} км")
    print(f"Полный маршрут: {trip_distance} км")
    print(f"Статус автомобиля: {'занят' if car_is_busy else 'свободен'}")
    print(f"ТО: {service_status}")
    print(f"Водитель: {driver_status}")
    print(f"Решение: {trip_status}")
    if fuel_required < 0:
        print("Топливо: расчет невозможен, проверьте расстояние и расход.")
    else:
        print(f"Расход на 100 км: {fuel_consumption:.1f} л")
        print(f"Плановая потребность в топливе: {fuel_required:.1f} л")
    if trip_status == "Поездка разрешена.":
        projected_mileage = mileage + trip_distance
        remaining_after_trip = (
            last_service_mileage + service_interval - projected_mileage
        )
        print(f"Пробег после поездки (прогноз): {projected_mileage} км")
        print(f"До ТО после поездки (прогноз): {remaining_after_trip} км")
    else:
        print("Перед назначением поездки устраните указанную причину запрета.")


if __name__ == "__main__":
    main()
