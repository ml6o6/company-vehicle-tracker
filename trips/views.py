# Отображение поездок и связей с автомобилями и водителями.

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import escape, format_html
from django.views.decorators.http import require_safe

from homepage.views import page
from models.trips import find_trip_by_id
from storage import load_data


@require_safe
def trips(request: HttpRequest) -> HttpResponse:
    """Показать активные и отмененные поездки из JSON."""
    _, _, trips_list = load_data(settings.BASE_DIR / "data")
    items = []
    for trip in trips_list:
        state = "отменена" if trip.is_cancelled else "активна"
        badge = "bg-secondary" if trip.is_cancelled else "bg-success"
        url = reverse("trips:trip_detail", args=[trip.id])
        items.append(str(format_html(
            '<li class="list-group-item py-3">'
            '<div class="d-flex flex-wrap justify-content-between gap-2">'
            '<a class="fw-semibold" href="{}">Поездка №{} · {}</a>'
            '<span class="badge {} align-self-center">{}</span></div>'
            '<p class="mb-0 text-secondary">{} · {} · {}</p></li>',
            url, trip.id, trip.trip_date, badge, state,
            trip.car.model, trip.car.plate, trip.driver.name,
        )))
    listing = "".join(items) or (
        '<li class="list-group-item">Поездок пока нет.</li>'
    )
    content = (
        '<h1>Поездки</h1>'
        f'<ul class="list-group">{listing}</ul>'
    )
    return HttpResponse(page("Поездки", content))


@require_safe
def trip_detail(request: HttpRequest, trip_id: int) -> HttpResponse:
    """Найти Trip и вывести атрибуты связанных Car и Driver."""
    _, _, trips_list = load_data(settings.BASE_DIR / "data")
    list_url = reverse("trips:trips")
    try:
        trip = find_trip_by_id(trips_list, trip_id)
    except (KeyError, ValueError):
        content = (
            '<h1 class="text-danger">Поездка не найдена</h1>'
            f'<a class="btn btn-outline-secondary" href="{list_url}">'
            'К списку поездок</a>'
        )
        return HttpResponse(page("Поездка не найдена", content), status=404)

    state = "отменена" if trip.is_cancelled else "активна"
    badge = "bg-secondary" if trip.is_cancelled else "bg-success"
    car_url = reverse("cars:car_detail", args=[trip.car.id])
    permission = "есть" if trip.driver.can_drive() else "нет"
    content = f"""
    <h1>Поездка №{trip.id}</h1>
    <div class="card"><div class="card-body">
        <dl class="row mb-0">
            <dt class="col-sm-4">Дата</dt>
            <dd class="col-sm-8">{trip.trip_date}</dd>
            <dt class="col-sm-4">Автомобиль</dt>
            <dd class="col-sm-8"><a href="{car_url}">
                {escape(trip.car.model)} · {escape(trip.car.plate)}
            </a></dd>
            <dt class="col-sm-4">Водитель</dt>
            <dd class="col-sm-8">{escape(trip.driver.name)}</dd>
            <dt class="col-sm-4">Допуск водителя</dt>
            <dd class="col-sm-8">{permission}</dd>
            <dt class="col-sm-4">Расстояние</dt>
            <dd class="col-sm-8">{trip.distance} км</dd>
            <dt class="col-sm-4">Пассажиров</dt>
            <dd class="col-sm-8">{trip.passengers}</dd>
            <dt class="col-sm-4">Требуется топлива</dt>
            <dd class="col-sm-8">{trip.calculate_fuel():.1f} л</dd>
            <dt class="col-sm-4">Статус</dt>
            <dd class="col-sm-8"><span class="badge {badge}">
                {state}
            </span></dd>
        </dl>
        <a class="btn btn-outline-secondary" href="{list_url}">
            К списку поездок
        </a>
    </div></div>
    """
    return HttpResponse(page(f"Поездка №{trip.id}", content))
