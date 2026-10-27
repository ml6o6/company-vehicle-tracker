# Отображение поездок через шаблоны и объекты предметной области

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe

from models.trips import find_trip_by_id
from storage import load_data


@require_safe
def trips(request: HttpRequest) -> HttpResponse:
    """Передать активные и отмененные поездки в шаблон списка."""
    _, _, trips_list = load_data(settings.BASE_DIR / "data")
    context = {"trips": trips_list}
    return render(request, "trips/trip_list.html", context)


@require_safe
def trip_detail(request: HttpRequest, trip_id: int) -> HttpResponse:
    """Передать Trip или None; сообщение об отсутствии выводит шаблон."""
    _, _, trips_list = load_data(settings.BASE_DIR / "data")
    try:
        trip = find_trip_by_id(trips_list, trip_id)
    except (KeyError, ValueError):
        trip = None

    context = {"trip": trip}
    if trip is not None:
        context["fuel_required"] = trip.calculate_fuel()
    return render(
        request, "trips/trip_detail.html", context,
        status=404 if trip is None else 200,
    )
