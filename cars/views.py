# Отображение автомобилей из SQLite через шаблоны Django

from contextlib import closing

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.timezone import localdate
from django.views.decorators.http import require_safe

from db.database import MAX_SQLITE_INTEGER, get_connection, load_queries
from utils import validate_date


@require_safe
def cars(request: HttpRequest) -> HttpResponse:
    """Показать автопарк или отобрать машины по вместимости."""
    capacity = request.GET.get("capacity", "")
    context = {"capacity": capacity, "cars": []}
    queries = load_queries()
    if capacity:
        try:
            minimum = int(capacity)
            if not 1 <= minimum <= MAX_SQLITE_INTEGER:
                raise ValueError
        except ValueError:
            context["error"] = "Укажите положительное целое число мест."
            return render(request, "cars/car_list.html", context)
        query, params = queries["cars_by_capacity"], (minimum,)
    else:
        query, params = queries["cars_list"], ()

    with closing(get_connection(settings.FLEET_DB_PATH)) as conn:
        context["cars"] = conn.execute(query, params).fetchall()
    return render(request, "cars/car_list.html", context)


@require_safe
def available(request: HttpRequest) -> HttpResponse:
    """Найти автомобили без активных поездок в выбранный день."""
    trip_date = request.GET.get("date", "")
    context = {"trip_date": trip_date, "cars": []}
    if "date" in request.GET:
        try:
            validate_date(trip_date)
        except ValueError:
            context["error"] = "Выберите существующую дату."
        else:
            query = load_queries()["available_cars"]
            with closing(get_connection(settings.FLEET_DB_PATH)) as conn:
                context["cars"] = conn.execute(query, (trip_date,)).fetchall()
    return render(request, "cars/available.html", context)


@require_safe
def car_detail(request: HttpRequest, car_id: int) -> HttpResponse:
    """Показать автомобиль, сведения о ТО и занятость сегодня."""
    today = localdate().isoformat()
    car = None
    if 1 <= car_id <= MAX_SQLITE_INTEGER:
        query = load_queries()["car_detail"]
        with closing(get_connection(settings.FLEET_DB_PATH)) as conn:
            car = conn.execute(query, (today, car_id)).fetchone()

    context = {"car": car, "today": today}
    if car is not None:
        context.update(available=bool(car["available"]),
                       service_remaining=car["service_remaining"])
    return render(request, "cars/car_detail.html", context,
                  status=404 if car is None else 200)
