# Проверки веб-слоя ПР5

import os
from datetime import date
from html.parser import HTMLParser

import django
import pytest
from django.test import Client, override_settings
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
