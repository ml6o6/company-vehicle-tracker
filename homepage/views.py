# Главная страница, общий HTML-каркас и страница ошибки 404

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.html import escape
from django.views.decorators.http import require_safe


def page(title: str, content: str) -> str:
    """Собрать HTML; content содержит разметку с экранированными данными."""
    bootstrap = (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.8"
        "/dist/css/bootstrap.min.css"
    )
    integrity = (
        "sha384-sRIl4kxILFvY47J16cr9ZwB07vP4J8+"
        "LH7qKQnuqkuIAvNWLzeN8tE5YBujZqJLB"
    )
    home_url = reverse("homepage:index")
    cars_url = reverse("cars:cars")
    trips_url = reverse("trips:trips")
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)} — Учет автомобилей</title>
    <link rel="stylesheet" href="{bootstrap}" integrity="{integrity}"
          crossorigin="anonymous">
    <style>
        body {{ background: #f5f7fa; color: #243247; }}
        .site-nav {{ background: #fff; border-bottom: 1px solid #dee2e6; }}
        .nav-link {{ font-weight: 500; }}
        main {{ padding-top: 2rem; padding-bottom: 3rem; }}
        h1 {{ margin-bottom: 1.5rem; overflow-wrap: anywhere; }}
        .card, .list-group {{ overflow-wrap: anywhere; }}
    </style>
</head>
<body>
    <header class="site-nav">
        <nav class="container nav flex-wrap py-3"
             aria-label="Основная навигация">
            <a class="nav-link" href="{home_url}">Главная</a>
            <a class="nav-link" href="{cars_url}">Автомобили</a>
            <a class="nav-link" href="{trips_url}">Поездки</a>
        </nav>
    </header>
    <main class="container">{content}</main>
</body>
</html>"""


@require_safe
def index(request: HttpRequest) -> HttpResponse:
    """Показать главную страницу через дочерний Django-шаблон."""
    return render(request, "homepage/index.html")


def page_not_found(request: HttpRequest, exception: Exception
                   ) -> HttpResponse:
    """Вернуть общую страницу 404 для неизвестного URL при DEBUG=False."""
    home_url = reverse("homepage:index")
    content = f"""
    <h1 class="text-danger">404 — страница не найдена</h1>
    <p>Проверьте адрес или вернитесь на главную.</p>
    <a class="btn btn-primary" href="{home_url}">На главную</a>
    """
    return HttpResponse(page("Страница не найдена", content), status=404)
