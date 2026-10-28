# Список автомобилей и карточка с числовым идентификатором.

from django.urls import path

from . import views

app_name = "cars"

urlpatterns = [
    path("", views.cars, name="cars"),
    path("available/", views.available, name="available"),
    path("<int:car_id>/", views.car_detail, name="car_detail"),
]
