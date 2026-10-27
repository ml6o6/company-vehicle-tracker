# Отображение автомобилей через шаблоны Django и контекст

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.timezone import localdate
from django.views.decorators.http import require_safe

from models.cars import find_car_by_id
from models.trips import is_car_available
from storage import load_cars, load_drivers, load_trips


@require_safe
def cars(request: HttpRequest) -> HttpResponse:
    """Передать объекты автомобилей в шаблон списка."""
    cars_list = load_cars(settings.BASE_DIR / "data" / "cars.json")
    context = {"cars": cars_list}
    return render(request, "cars/car_list.html", context)


@require_safe
def car_detail(request: HttpRequest, car_id: int) -> HttpResponse:
    """Передать автомобиль или None; сообщение об отсутствии выводит шаблон."""
    directory = settings.BASE_DIR / "data"
    cars_list = load_cars(directory / "cars.json")
    try:
        car = find_car_by_id(cars_list, car_id)
    except (KeyError, ValueError):
        car = None

    context = {"car": car}
    if car is not None:
        drivers = load_drivers(directory / "drivers.json")
        trips = load_trips(directory / "trips.json", cars_list, drivers)
        today = localdate().isoformat()
        context.update({
            "today": today,
            "available": is_car_available(trips, car, today),
            "service_remaining": car.service_remaining(),
        })
    return render(
        request, "cars/car_detail.html", context,
        status=404 if car is None else 200,
    )
