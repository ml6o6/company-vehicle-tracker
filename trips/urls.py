# Список поездок и карточка с числовым идентификатором.

from django.urls import path

from . import views

app_name = "trips"

urlpatterns = [
    path("", views.trips, name="trips"),
    path("<int:trip_id>/", views.trip_detail, name="trip_detail"),
]
