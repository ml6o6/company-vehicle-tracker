# Списки, карточки и статистика поездок из SQLite

from contextlib import closing

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe

from db.database import MAX_SQLITE_INTEGER, get_connection, load_queries


@require_safe
def trips(request: HttpRequest) -> HttpResponse:
    """Показать все поездки или только активные."""
    active_only = request.GET.get("status") == "active"
    name = "active_trips" if active_only else "trips_list"
    with closing(get_connection(settings.FLEET_DB_PATH)) as conn:
        rows = conn.execute(load_queries()[name]).fetchall()
    return render(request, "trips/trip_list.html",
                  {"trips": rows, "active_only": active_only})


@require_safe
def trip_detail(request: HttpRequest, trip_id: int) -> HttpResponse:
    """Показать поездку, автомобиль и водителя."""
    trip = None
    if 1 <= trip_id <= MAX_SQLITE_INTEGER:
        query = load_queries()["trip_detail"]
        with closing(get_connection(settings.FLEET_DB_PATH)) as conn:
            trip = conn.execute(query, (trip_id,)).fetchone()
    return render(request, "trips/trip_detail.html", {"trip": trip},
                  status=404 if trip is None else 200)


@require_safe
def statistics(request: HttpRequest) -> HttpResponse:
    """Показать итоги и число активных поездок по машинам и водителям."""
    min_trips = request.GET.get("min_trips", "")
    context = {"min_trips": min_trips}
    try:
        minimum = int(min_trips or "0")
        if not 0 <= minimum <= MAX_SQLITE_INTEGER:
            raise ValueError
    except ValueError:
        context["error"] = "Укажите целое число поездок от нуля."

    queries = load_queries()
    with closing(get_connection(settings.FLEET_DB_PATH)) as conn:
        conn.execute("BEGIN")
        context["totals"] = conn.execute(queries["trip_totals"]).fetchone()
        context["distance"] = conn.execute(
            queries["active_distance"]
        ).fetchone()
        context["by_car"] = conn.execute(queries["trips_by_car"]).fetchall()
        if "error" not in context:
            context["by_driver"] = conn.execute(
                queries["trips_by_driver"], (minimum,)
            ).fetchall()
    return render(request, "trips/statistics.html", context)
