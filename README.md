# Имотен регистър

Обяви за апартаменти и къщи, брокери и запитвания. Flask и Gunicorn, PostgreSQL, Nginx с две реплики, RabbitMQ с отделен worker, Dozzle.

Сайт: https://localhost:8443
HTTP :8080 пренасочва към HTTPS. Сертификатът е self-signed.

## Команди

Всички команди са от папката на проекта.

### Docker: пускане, спиране, рестарт, изтриване

```bash
docker compose up --build -d
docker compose stop
docker compose start
docker compose restart
docker compose restart web worker
docker compose ps
docker compose logs -f
docker compose logs -f nginx web worker
docker compose down
docker compose down -v
```

`stop` спира контейнерите и пази данните. `start` ги пуска пак. `restart` ги рестартира. `down` маха контейнерите и мрежата, volume-ът с базата остава. `down -v` трие и базата.

Един случаен ред в Активност не се чисти с `down`. Той е ред в таблицата `listing_events` и остава и след изтриване на обявата.

### psql: таблици и данни

```bash
docker compose exec db psql -U postgres -d imoti -c '\dt'
docker compose exec db psql -U postgres -d imoti -c 'SELECT id, name, office, email FROM agents ORDER BY id;'
docker compose exec db psql -U postgres -d imoti -c 'SELECT id, kind, title, city, price_eur, area_sqm, status FROM listings ORDER BY id;'
docker compose exec db psql -U postgres -d imoti -c 'SELECT id, listing_id, author_name, phone, message FROM inquiries ORDER BY id;'
docker compose exec db psql -U postgres -d imoti -c 'SELECT id, logged_at, event, listing_id, title FROM listing_events ORDER BY id;'
```

Изтриване само на случайния запис от снимката (заглавие `tfhfthf`, обява 10):

```bash
docker compose exec db psql -U postgres -d imoti -c "DELETE FROM listing_events WHERE title = 'tfhfthf';"
```

Ако редът е друг, първо виж `id` от SELECT и после:

```bash
docker compose exec db psql -U postgres -d imoti -c 'DELETE FROM listing_events WHERE id = 1;'
```

Интерактивно:

```bash
docker compose exec db psql -U postgres -d imoti
```

### pytest

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
```

### HTTP заявки

`-k` приема self-signed сертификата.

```bash
curl -k https://localhost:8443/api/listings
curl -k https://localhost:8443/api/listings/1
curl -k https://localhost:8443/api/agents
curl -k https://localhost:8443/api/inquiries
curl -k https://localhost:8443/api/events

curl -k -X POST https://localhost:8443/api/agents \
  -H 'Content-Type: application/json' \
  -d '{"name":"Иван Иванов","phone":"+359881112233","email":"ivan.ivanov@imoti.bg","office":"Бургас"}'

curl -k -X PUT https://localhost:8443/api/agents/1 \
  -H 'Content-Type: application/json' \
  -d '{"name":"Мария Георгиева","phone":"+359884102210","email":"maria.georgieva@imoti.bg","office":"София"}'

curl -k -X DELETE https://localhost:8443/api/agents/4

curl -k -X POST https://localhost:8443/api/listings \
  -H 'Content-Type: application/json' \
  -d '{"kind":"apartment","title":"Двустаен в Центъра","description":"Южен.","deal_type":"sale","price_eur":120000,"area_sqm":60,"city":"София","address":"ул. Тест 1","year_built":2010,"status":"active","agent_id":1,"rooms":2,"floor":3,"total_floors":6,"has_elevator":true,"has_balcony":false}'

curl -k -X PUT https://localhost:8443/api/listings/1 \
  -H 'Content-Type: application/json' \
  -d '{"title":"Двустаен в Лозенец","description":"Южен.","deal_type":"sale","price_eur":198000,"area_sqm":78,"city":"София","address":"ул. Цветна 12","year_built":2014,"status":"active","agent_id":1,"rooms":2,"floor":4,"total_floors":8,"has_elevator":true,"has_balcony":true}'

curl -k -X DELETE https://localhost:8443/api/listings/10

curl -k -X POST https://localhost:8443/api/listings/1/inquiries \
  -H 'Content-Type: application/json' \
  -d '{"author_name":"Анна Маринова","phone":"+359881112233","message":"Свободна ли е в събота?"}'

curl -k -X PUT https://localhost:8443/api/inquiries/1 \
  -H 'Content-Type: application/json' \
  -d '{"author_name":"Анна Маринова","phone":"+359881112233","message":"Още свободна ли е?"}'

curl -k -X DELETE https://localhost:8443/api/inquiries/1
```

Други адреси: http://localhost:9999 Dozzle, http://localhost:15672 RabbitMQ (`imoti` / `rabbitpass`).

## Състав

- `app/pages` рисува страниците. `app/api` връща JSON на `/api`.
- `app/services` проверява данните и пуска събитие.
- `app/repositories` чете и пише през SQLAlchemy.
- `app/models.py` е схема: `Agent`, `Listing`, `Apartment`, `House`, `Inquiry`, `ListingEvent`.
- `Listing` е базов клас. Апартаментът и къщата са отделни таблици към него.
- Цена на квадратен метър е цена / площ на имота. Дворът не влиза.
- Запитването се трие заедно с обявата. Редът в Активност остава.
- `app/worker.py` слуша опашка `imoti_log` и пише в `listing_events`.
- `nginx` раздава към две реплики `web`. Сертификатът се генерира в образа, `CN=localhost`.
- Паролите са в `.env`. Примерен файл: `.env.example`.
- При празна база `app/seed.py` слага три брокера и девет обяви.

Страници: `/` начало, `/listings` обяви, `/agents` брокери, `/inquiries` запитвания, `/journal` активност.

Диаграма: [docs/class-diagram.svg](docs/class-diagram.svg). Слайдове: [docs/presentation.html](docs/presentation.html).
