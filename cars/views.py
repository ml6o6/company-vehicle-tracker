# Отображение автомобилей и проверка занятости средствами ПР3

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import escape, format_html
from django.utils.timezone import localdate
from django.views.decorators.http import require_safe

from homepage.views import page
from models.cars import find_car_by_id
from models.trips import is_car_available
from storage import load_cars, load_drivers, load_trips


@require_safe
def cars(request: HttpRequest) -> HttpResponse:
    """Загрузить автомобили из JSON и показать ссылки на их карточки."""
    cars_list = load_cars(settings.BASE_DIR / "data" / "cars.json")
    items = []
    for car in cars_list:
        url = reverse("cars:car_detail", args=[car.id])
        items.append(str(format_html(
            '<li class="list-group-item py-3">'
            '<a class="fw-semibold" href="{}">{} · {}</a>'
            '<p class="mb-0 text-secondary">Пассажирских мест: {} · '
            'Пробег: {} км</p></li>',
            url, car.model, car.plate, car.capacity, car.mileage,
        )))
    listing = "".join(items) or (
        '<li class="list-group-item">Автомобилей пока нет.</li>'
    )
    content = (
        '<h1>Автомобили</h1>'
        f'<ul class="list-group">{listing}</ul>'
    )
    return HttpResponse(page("Автомобили", content))


@require_safe
def car_detail(request: HttpRequest, car_id: int) -> HttpResponse:
    """Найти Car по ID и показать параметры ТО и занятость сегодня."""
    directory = settings.BASE_DIR / "data"
    cars_list = load_cars(directory / "cars.json")
    list_url = reverse("cars:cars")
    try:
        car = find_car_by_id(cars_list, car_id)
    except (KeyError, ValueError):
        content = (
            '<h1 class="text-danger">Автомобиль не найден</h1>'
            f'<a class="btn btn-outline-secondary" href="{list_url}">'
            'К списку автомобилей</a>'
        )
        return HttpResponse(page("Автомобиль не найден", content), status=404)

    drivers = load_drivers(directory / "drivers.json")
    trips = load_trips(directory / "trips.json", cars_list, drivers)
    today = localdate().isoformat()
    available = is_car_available(trips, car, today)
    state = "свободен" if available else "занят"
    badge = "bg-success" if available else "bg-danger"
    content = f"""
    <h1>{escape(car.model)}</h1>
    <div class="card"><div class="card-body">
        <dl class="row mb-0">
            <dt class="col-sm-5">ID</dt>
            <dd class="col-sm-7">{car.id}</dd>
            <dt class="col-sm-5">Госномер</dt>
            <dd class="col-sm-7">{escape(car.plate)}</dd>
            <dt class="col-sm-5">Пассажирских мест</dt>
            <dd class="col-sm-7">{car.capacity} (без водителя)</dd>
            <dt class="col-sm-5">Пробег</dt>
            <dd class="col-sm-7">{car.mileage} км</dd>
            <dt class="col-sm-5">Расход топлива</dt>
            <dd class="col-sm-7">{car.fuel_consumption:g} л / 100 км</dd>
            <dt class="col-sm-5">Последнее ТО</dt>
            <dd class="col-sm-7">{car.maintenance.last_mileage} км</dd>
            <dt class="col-sm-5">Интервал ТО</dt>
            <dd class="col-sm-7">{car.maintenance.interval} км</dd>
            <dt class="col-sm-5">Остаток до ТО по пробегу</dt>
            <dd class="col-sm-7">{car.service_remaining()} км</dd>
        </dl>
        <p>Занятость на сегодня ({today}):
            <span class="badge {badge}">{state}</span>
        </p>
        <a class="btn btn-outline-secondary" href="{list_url}">
            К списку автомобилей
        </a>
    </div></div>
    """
    return HttpResponse(page(car.model, content))
