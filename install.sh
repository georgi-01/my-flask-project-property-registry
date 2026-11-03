#!/bin/sh
set -eu
cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
  echo "Липсва Docker. Инсталирай Docker Desktop или Docker Engine и опитай пак."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Липсва Docker Compose v2. Нужна е командата: docker compose"
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Създаден е .env от .env.example. Паролите са само за демонстрация."
fi

echo "Сглобяване и стартиране..."
docker compose up --build -d
echo
echo "Готово."
echo "Сайт:    https://localhost:8443"
echo "Dozzle:  http://localhost:9999"
echo "RabbitMQ: http://localhost:15672  (потребител и парола са в .env)"
echo
echo "Логове: docker compose logs -f"
echo "Спиране: docker compose down"
