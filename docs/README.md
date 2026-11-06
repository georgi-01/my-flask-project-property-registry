# Имотен регистър

Обяви за апартаменти и къщи, брокери и запитвания. Flask и Gunicorn, PostgreSQL, Nginx с две реплики, RabbitMQ с отделен worker, Dozzle.

## Стартиране

Командите са от папката на проекта. На двете системи се стартират различни файлове.

За Linux се стартира `install.sh`:

```bash
./install.sh
```

За Windows се стартира `install.bat`:

```bat
.\install.bat
```

И двата файла проверяват Docker, създават `.env.example` и `.env`, ако липсват, и пускат `docker compose up --build -d`.

Сайт: https://localhost:8443
HTTP :8080 пренасочва към HTTPS. Сертификатът е self-signed.

Dozzle: http://localhost:9999
RabbitMQ: http://localhost:15672, потребител `imoti`, парола `rabbitpass`.

## Конфигурация

### requirements

`requirements.txt` е за работещото приложение: Flask, Gunicorn, SQLAlchemy, драйверът `psycopg2-binary`, `python-dotenv` и `pika` за опашката.

`requirements-dev.txt` включва същия файл и добавя pytest. Ползва се само при тестовете на машината, не в контейнера.

### Pytest

`pytest.ini` търси тестовете в `tests/` и слага корена на проекта в пътя за импортите. Тестовете ползват временен SQLite файл и не пускат RabbitMQ.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
```

### Docker

`compose.yaml` вдига шестте услуги. Образът на приложението се строи от `Dockerfile`: Python 3.13, пакетите от `requirements.txt` и Gunicorn на порт 8000.

#### db

PostgreSQL 18. Името на базата и паролата идват от `.env`: `PGDATABASE` и `PGPASSWORD`. По подразбиране базата е `imoti`, потребителят е `postgres`, паролата е `imotipass`. Данните се пазят във volume `pgdata`. Услугата има healthcheck и web и worker чакат тя да е готова. Порт към машината няма. Влиза се с `docker compose exec`.

#### rabbitmq

RabbitMQ 4 с management интерфейс. Потребителят и паролата са `RABBITMQ_USER` и `RABBITMQ_PASSWORD` от `.env`. Порт 5672 е за опашката, 15672 е за уеб конзолата. Worker чака healthcheck-а на брокера.

#### web

Две реплики на образа `imoti-web`. Вземат `.env` и пренасочват `PGHOST` към услугата `db` и `RABBITMQ_HOST` към `rabbitmq`. Нямат публикуван порт. Nginx ги стига по вътрешното име `web`.

#### worker

Същият образ, команда `python -m app.worker`. Слуша опашката `imoti_log` и пише редовете в `listing_events`. Една реплика, рестартира се сама.

#### nginx

Собствен образ от `nginx/`. Прави self-signed сертификат за `localhost`. Слуша 8080 и 8443 на машината. Порт 80 вътре пренасочва към HTTPS на 8443. Порт 443 разпределя заявките към двете web реплики и при отказ на едната пробва другата.

#### dozzle

Чете Docker socket-а и показва логовете на контейнерите. На машината е на порт 9999. Не е страница в сайта.

#### volumes

`pgdata` държи файловете на PostgreSQL. `docker compose down` маха контейнерите, но не и volume-а. `docker compose down -v` трие и базата.

## Компоненти

### База данни

При старт SQLAlchemy създава таблиците, ако ги няма. `agents` пази брокерите. `listings` е общият ред на обявата. `apartments` и `houses` допълват същия номер с полетата на апартамент или къща. `inquiries` са запитванията и се трият заедно с обявата. `listing_events` е журнал. Там `listing_id` не е външен ключ, затова редът остава и след изтрита обява. `app/seed.py` пълни празна база с примерни брокери и обяви.

### ORM модели

Моделите са в `app/models.py`. `Agent`, `Inquiry` и `ListingEvent` са отделни класове. `Listing` е базовият клас на обявата. `Apartment` и `House` го наследяват и имат собствени таблици. `price_per_sqm` не е колона. Смята се от цената и площта на имота. Дворът не влиза. `to_dict()` събира полетата за JSON и за събитието към опашката. Връзката към базата е в `app/db.py`.

### Тестовете с pytest

`tests/test_services.py` минава през бизнес слоя: цена на квадратен метър, двор само при къща, етаж в сградата, отказ при лоши данни и при изтриване на брокер с обяви. `tests/test_repository.py` записва апартамент и къща и ги прочита обратно през двете таблици. `tests/test_api.py` пуска HTTP клиента на Flask: начални данни, създаване и изтриване, отказ на грешна обява, страниците и повторен имейл на брокер.

### Бизнес слой

`app/services` проверява формуляра и вика хранилището. `ListingService` създава, променя, трие и търси обяви и брои записите за началото. `AgentService` прави същото за брокери и не трие брокер, който има обяви. `InquiryService` пази запитванията към съществуваща обява. `EventService` чете последните редове от журнала. След запис, промяна или изтриване на обява или запитване услугата публикува съобщение през `app/events.py`. Ако `RABBITMQ_ENABLED` е `0`, публикуването се пропуска.

`app/repositories` само чете и пише. Не валидира. Общият `Repository` държи сесията. Отделни класове има за обяви, брокери, запитвания и събития.

### API

`app/api` връща JSON под `/api`. `listings` обслужва списък, една обява, създаване, промяна и изтриване. Запитване към обява се пуска на `/api/listings/<id>/inquiries`. `agents` и `inquiries` имат същите четири операции. `events` е само четене на журнала. Формуляр от страница ползва скрито поле `_method`, за да прати PUT и DELETE през POST.

### Pages

`app/pages` рисува HTML със същите услуги. Началото показва броя на обявите, брокерите и запитванията. Обява, брокер и запитване се отварят, създават и редактират. Журналът е на `/activity`.

### Templates

Шаблоните са в `app/templates`. `base.html` е обвивката: горен ред и долен ред. `home.html`, `listings.html`, `listing.html` и `listing_form.html` са обявите. `agents.html`, `agent.html` и `agent_form.html` са брокерите. `inquiries.html` и `inquiry_form.html` са запитванията. `journal.html` е активността. `_card.html`, `_fields.html`, `_hints.html` и `_icons.html` се включват в останалите.

### Static

`app/static/style.css` е видът на страниците. `form.js` праща формуляра за редакция и изтриване. `fields.js` ограничава полетата по тип. `favicon.svg` и `houses.svg` са иконите.

## Полезни команди

Всички са от папката на проекта.

### docker compose

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

`stop` спира контейнерите и пази данните. `start` ги пуска пак. `restart` ги рестартира. `down` маха контейнерите и мрежата. `down -v` трие и volume-а с базата.

### psql

```bash
docker compose exec db psql -U postgres -d imoti -c '\dt'
docker compose exec db psql -U postgres -d imoti -c 'SELECT id, name, office, email FROM agents ORDER BY id;'
docker compose exec db psql -U postgres -d imoti -c 'SELECT id, kind, title, city, price_eur, area_sqm, status FROM listings ORDER BY id;'
docker compose exec db psql -U postgres -d imoti -c 'SELECT id, rooms, floor, total_floors FROM apartments ORDER BY id;'
docker compose exec db psql -U postgres -d imoti -c 'SELECT id, floors, yard_sqm, has_garage FROM houses ORDER BY id;'
docker compose exec db psql -U postgres -d imoti -c 'SELECT id, listing_id, author_name, phone, message FROM inquiries ORDER BY id;'
docker compose exec db psql -U postgres -d imoti -c 'SELECT id, logged_at, event, listing_id, title FROM listing_events ORDER BY id;'
docker compose exec db psql -U postgres -d imoti -c 'DELETE FROM listing_events WHERE id = 1;'
docker compose exec db psql -U postgres -d imoti
```

### curl

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
