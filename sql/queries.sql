-- Именованные запросы сайта. Значения передаются параметрами ?.

-- name: cars_list
-- Список автомобилей.
SELECT id, model, plate, capacity, mileage
FROM cars
ORDER BY id;

-- name: trips_list
-- Список поездок с участниками, включая отмененные.
SELECT t.id, t.trip_date, t.is_cancelled, c.model AS car_model,
       c.plate AS car_plate, d.name AS driver_name
FROM trips AS t
JOIN cars AS c ON c.id = t.car_id
JOIN drivers AS d ON d.id = t.driver_id
ORDER BY t.id;

-- name: cars_by_capacity
-- Автомобили от заданного количества пассажирских мест.
SELECT id, model, plate, capacity, mileage
FROM cars
WHERE capacity >= ?
ORDER BY capacity, id;

-- name: available_cars
-- Автомобили без активной поездки в выбранную дату.
SELECT c.id, c.model, c.plate, c.capacity, c.mileage
FROM cars AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM trips AS t
    WHERE t.car_id = c.id AND t.trip_date = ? AND t.is_cancelled = 0
)
ORDER BY c.id;

-- name: car_detail
-- Карточка автомобиля: ТО и занятость на переданную дату; затем ID.
SELECT c.id, c.model, c.plate, c.capacity, c.mileage, c.fuel_consumption,
       m.last_mileage, m.interval,
       m.last_mileage + m.interval - c.mileage AS service_remaining,
       NOT EXISTS (
           SELECT 1
           FROM trips AS t
           WHERE t.car_id = c.id AND t.trip_date = ? AND t.is_cancelled = 0
       ) AS available
FROM cars AS c
JOIN maintenance AS m ON m.car_id = c.id
WHERE c.id = ?;

-- name: active_trips
-- Активные поездки с автомобилями и водителями.
SELECT t.id, t.trip_date, t.is_cancelled, c.model AS car_model,
       c.plate AS car_plate, d.name AS driver_name
FROM trips AS t
JOIN cars AS c ON c.id = t.car_id
JOIN drivers AS d ON d.id = t.driver_id
WHERE t.is_cancelled = 0
ORDER BY t.trip_date, t.id;

-- name: trip_detail
-- Поездка по ID со связанными данными и расчетным расходом топлива.
SELECT t.id, t.trip_date, t.distance, t.passengers, t.is_cancelled,
       c.id AS car_id, c.model AS car_model, c.plate AS car_plate,
       d.name AS driver_name, d.has_permission,
       t.distance * c.fuel_consumption / 100.0 AS fuel_required
FROM trips AS t
JOIN cars AS c ON c.id = t.car_id
JOIN drivers AS d ON d.id = t.driver_id
WHERE t.id = ?;

-- name: trip_totals
-- Число всех, активных и отмененных поездок.
SELECT COUNT(*) AS total,
       COUNT(CASE WHEN is_cancelled = 0 THEN 1 END) AS active,
       COUNT(CASE WHEN is_cancelled = 1 THEN 1 END) AS cancelled
FROM trips;

-- name: active_distance
-- Общая и средняя длина маршрутов активных поездок.
SELECT COALESCE(SUM(distance), 0) AS total_distance,
       COALESCE(AVG(distance), 0) AS average_distance
FROM trips
WHERE is_cancelled = 0;

-- name: trips_by_car
-- Активные поездки по автомобилям, включая автомобили без поездок.
SELECT c.id, c.model, c.plate, COUNT(t.id) AS trip_count
FROM cars AS c
LEFT JOIN trips AS t ON t.car_id = c.id AND t.is_cancelled = 0
GROUP BY c.id, c.model, c.plate
ORDER BY trip_count DESC, c.id;

-- name: trips_by_driver
-- Активные поездки по водителям с заданным порогом количества.
SELECT d.name, COUNT(t.id) AS trip_count
FROM drivers AS d
LEFT JOIN trips AS t ON t.driver_id = d.id AND t.is_cancelled = 0
GROUP BY d.id, d.name
HAVING COUNT(t.id) >= ?
ORDER BY trip_count DESC, d.id;
