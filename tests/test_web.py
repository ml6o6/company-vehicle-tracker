# Проверки веб-слоя и шаблонов ПР6

import os
from datetime import date
from html.parser import HTMLParser

import django
import pytest
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import Client, override_settings
from django.test.utils import setup_test_environment, teardown_test_environment
from django.urls import resolve, reverse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vehicle_site.settings")
django.setup()

from models import Car, Driver, Trip  # noqa: E402
from storage import save_cars, save_drivers, save_trips  # noqa: E402


@pytest.fixture
def web(tmp_path, monkeypatch):
    """Подготовить связанные объекты только во временном каталоге."""
    cars = [
        Car(1, "Lada Vesta", "А123ВС77", 4, 48000, 40000, 10000, 8.5),
        Car(2, "ГАЗель NEXT", "В456ЕК77", 12, 25000, 20000, 10000, 12.0),
    ]
    drivers = [Driver(1, "Иванов Иван Иванович", True),
               Driver(2, "Петров Петр Петрович", True)]
    trips = [
        Trip(1, cars[1], drivers[1], "2026-11-10", 90, 8),
        Trip(2, cars[0], drivers[0], "2026-11-10", 120, 2, True),
    ]
    directory = tmp_path / "data"
    save_cars(directory / "cars.json", cars)
    save_drivers(directory / "drivers.json", drivers)
    save_trips(directory / "trips.json", trips)
    monkeypatch.setattr("cars.views.localdate", lambda: date(2026, 11, 10))
    with override_settings(BASE_DIR=tmp_path, DEBUG=False,
                           ALLOWED_HOSTS=["testserver"]):
        yield Client(), directory, cars, drivers


@pytest.mark.parametrize("url, text", [
    ("/", "Сервис учета автомобилей организации"),
    ("/cars/", "Lada Vesta"),
    ("/cars/1/", "А123ВС77"),
    ("/trips/", "ГАЗель NEXT"),
    ("/trips/1/", "Петров Петр Петрович"),
])
def test_pages(web, url, text):
    client, _, _, _ = web
    response = client.get(url)
    assert response.status_code == 200
    html = response.content.decode()
    assert text in html
    assert '<html lang="ru">' in html
    assert '<meta name="viewport"' in html
    assert "bootstrap@5.3." in html
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"


def test_dynamic_routes():
    assert resolve("/cars/17/").kwargs == {"car_id": 17}
    assert resolve("/trips/28/").kwargs == {"trip_id": 28}
    assert reverse("cars:car_detail", args=[1]) == "/cars/1/"
    assert reverse("trips:trip_detail", args=[1]) == "/trips/1/"


@pytest.mark.parametrize("url, text", [
    ("/cars/999/", "Автомобиль не найден"),
    ("/cars/0/", "Автомобиль не найден"),
    ("/trips/999/", "Поездка не найдена"),
    ("/trips/0/", "Поездка не найдена"),
    ("/cars/abc/", "404 — страница не найдена"),
    ("/trips/abc/", "404 — страница не найдена"),
    ("/nonexistent/", "404 — страница не найдена"),
])
def test_missing_resources(web, url, text):
    client, _, _, _ = web
    response = client.get(url)
    assert response.status_code == 404
    assert text in response.content.decode()
    assert 'href="/"' in response.content.decode()


def test_not_found_with_debug(web):
    client, _, _, _ = web
    with override_settings(DEBUG=True):
        assert "Автомобиль не найден" in client.get(
            "/cars/999/").content.decode()
        assert "Поездка не найдена" in client.get(
            "/trips/999/").content.decode()
        assert client.get("/nonexistent/").status_code == 404


def test_availability_uses_active_trips(web):
    client, _, _, _ = web
    assert "свободен" in client.get("/cars/1/").content.decode()
    assert "занят</span>" in client.get("/cars/2/").content.decode()
    assert "2026-11-10" in client.get("/cars/2/").content.decode()


def test_trip_status_and_object_links(web):
    client, _, _, _ = web
    html = client.get("/trips/").content.decode()
    assert "активна" in html
    assert "отменена" in html
    active = client.get("/trips/1/").content.decode()
    assert 'href="/cars/2/"' in active
    assert "Петров Петр Петрович" in active
    assert "10.8 л" in active
    cancelled = client.get("/trips/2/").content.decode()
    assert "bg-secondary" in cancelled
    assert "отменена" in cancelled


def test_json_changes_visible_without_restart(web):
    client, directory, cars, _ = web
    assert "Lada Vesta" in client.get("/cars/1/").content.decode()
    cars[0].model = "Обновленная модель"
    save_cars(directory / "cars.json", cars)
    assert "Обновленная модель" in client.get("/cars/1/").content.decode()


def test_json_values_escaped(web):
    client, directory, cars, drivers = web
    cars[1].model = "<script>alert(1)</script>"
    drivers[1].name = '<img src=x onerror="alert(1)">'
    save_cars(directory / "cars.json", cars)
    save_drivers(directory / "drivers.json", drivers)
    for url in ("/cars/", "/cars/2/", "/trips/", "/trips/1/"):
        html = client.get(url).content.decode()
        assert "<script>alert(1)</script>" not in html
        assert "<img src=x" not in html
        assert "&lt;script&gt;" in html


def test_empty_collections(web):
    client, directory, _, _ = web
    save_cars(directory / "cars.json", [])
    save_drivers(directory / "drivers.json", [])
    save_trips(directory / "trips.json", [])
    assert "Автомобилей пока нет" in client.get("/cars/").content.decode()
    assert "Поездок пока нет" in client.get("/trips/").content.decode()
    assert client.get("/cars/1/").status_code == 404
    assert client.get("/trips/1/").status_code == 404


def test_navigation_and_read_only(web):
    client, directory, _, _ = web

    class Links(HTMLParser):
        def __init__(self):
            super().__init__()
            self.urls = []

        def handle_starttag(self, tag, attrs):
            if tag == "a":
                self.urls.append(dict(attrs)["href"])

    before = {p.name: p.read_bytes() for p in directory.glob("*.json")}
    for url in ("/", "/cars/", "/cars/1/", "/trips/", "/trips/1/"):
        parser = Links()
        parser.feed(client.get(url).content.decode())
        assert {"/", "/cars/", "/trips/"} <= set(parser.urls)
        for link in parser.urls:
            assert client.get(link).status_code == 200
        assert client.head(url).status_code == 200
        assert client.post(url).status_code == 405
    assert before == {p.name: p.read_bytes()
                      for p in directory.glob("*.json")}


@pytest.fixture
def template_environment():
    """Включить захват шаблонов и контекста штатными средствами Django."""
    setup_test_environment()
    try:
        yield
    finally:
        teardown_test_environment()


@pytest.mark.parametrize("url, template, status", [
    ("/", "homepage/index.html", 200),
    ("/cars/", "cars/car_list.html", 200),
    ("/cars/1/", "cars/car_detail.html", 200),
    ("/cars/999/", "cars/car_detail.html", 404),
    ("/cars/0/", "cars/car_detail.html", 404),
    ("/trips/", "trips/trip_list.html", 200),
    ("/trips/1/", "trips/trip_detail.html", 200),
    ("/trips/999/", "trips/trip_detail.html", 404),
    ("/trips/0/", "trips/trip_detail.html", 404),
    ("/nonexistent/", "404.html", 404),
])
def test_template_inheritance(web, template_environment,
                              url, template, status):
    client, _, _, _ = web
    response = client.get(url)
    names = {item.name for item in response.templates}
    assert response.status_code == status
    assert {template, "base.html",
            "includes/navigation.html"} <= names
    html = response.content.decode()
    assert 'href="/static/homepage/css/style.css"' in html
    assert 'src="/static/homepage/img/logo.svg"' in html
    assert 'src="/static/homepage/js/main.js"' in html
    assert 'id="current-year"' in html
    if url == "/cars/":
        assert "cars/includes/car_card.html" in names
        assert 'href="/cars/1/"' in response.content.decode()
        assert 'href="/cars/2/"' in response.content.decode()


def test_car_objects_and_missing_context(web, template_environment):
    client, _, _, _ = web
    listing = client.get("/cars/")
    assert all(isinstance(car, Car) for car in listing.context["cars"])
    detail = client.get("/cars/2/")
    car = detail.context["car"]
    assert isinstance(car, Car)
    assert car.id == 2
    assert detail.context["available"] is False
    assert detail.context["service_remaining"] == 5000
    assert "занят</span>" in detail.content.decode()
    missing = client.get("/cars/999/")
    assert missing.context["car"] is None
    assert missing.status_code == 404


def test_trip_context_and_shared_status(web, template_environment):
    client, _, _, _ = web
    listing = client.get("/trips/")
    assert all(isinstance(trip, Trip) for trip in listing.context["trips"])
    assert "trips/includes/trip_status.html" in {
        item.name for item in listing.templates
    }
    for trip_id, cancelled in ((1, False), (2, True)):
        detail = client.get(f"/trips/{trip_id}/")
        trip = detail.context["trip"]
        assert isinstance(trip.car, Car)
        assert isinstance(trip.driver, Driver)
        assert trip.is_cancelled is cancelled
        assert "trips/includes/trip_status.html" in {
            item.name for item in detail.templates
        }
    missing = client.get("/trips/999/")
    assert missing.context["trip"] is None
    assert missing.status_code == 404


def test_template_count_filters(web):
    client, directory, _, _ = web
    assert "Всего автомобилей: 2" in client.get("/cars/").content.decode()
    assert "Всего поездок: 2" in client.get("/trips/").content.decode()
    save_cars(directory / "cars.json", [])
    save_trips(directory / "trips.json", [])
    assert "Всего автомобилей: 0" in client.get("/cars/").content.decode()
    assert "Всего поездок: 0" in client.get("/trips/").content.decode()


def test_default_filter_preserves_model_validation(web):
    _, _, cars, _ = web
    cars[0].model = ""
    html = render_to_string("cars/includes/car_card.html", {"car": cars[0]})
    assert "Без названия" in html
    with pytest.raises(ValueError):
        Car(3, "", "Т123ЕС77", 4, 1000, 0, 10000, 7.5)


@pytest.mark.parametrize("name", [
    "homepage/css/style.css",
    "homepage/js/main.js",
    "homepage/img/logo.svg",
])
def test_static_files_discovered(name):
    assert finders.find(name) is not None
