# Главная страница и обработчик 404 на Django-шаблонах

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe


@require_safe
def index(request: HttpRequest) -> HttpResponse:
    """Показать главную страницу через дочерний Django-шаблон."""
    return render(request, "homepage/index.html")


def page_not_found(request: HttpRequest, exception: Exception
                   ) -> HttpResponse:
    """Показать общую страницу ошибки 404 при DEBUG=False."""
    return render(request, "404.html", status=404)
