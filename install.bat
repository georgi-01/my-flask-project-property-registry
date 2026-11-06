@echo off
cd /d "%~dp0"

where docker >nul 2>&1
if errorlevel 1 (
  echo Docker is not available. Start Docker Desktop and try again.
  exit /b 1
)

docker compose version >nul 2>&1
if errorlevel 1 (
  echo Docker Compose is missing. The command "docker compose" is required.
  exit /b 1
)

if not exist ".env.example" (
  > ".env.example" (
    echo PGHOST=localhost
    echo PGPORT=5432
    echo PGUSER=postgres
    echo PGPASSWORD=imotipass
    echo PGDATABASE=imoti
    echo SECRET_KEY=change-this-key
    echo RABBITMQ_HOST=localhost
    echo RABBITMQ_USER=imoti
    echo RABBITMQ_PASSWORD=rabbitpass
    echo RABBITMQ_ENABLED=1
  )
  echo Created .env.example
)

if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
  echo Created .env
)

echo Building and starting...
docker compose --env-file ".env" up --build -d
if errorlevel 1 exit /b 1

echo.
echo Site:     https://localhost:8443
echo Dozzle:   http://localhost:9999
echo RabbitMQ: http://localhost:15672