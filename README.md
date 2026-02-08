# mmWave Sensor API

## Overview
This API receives sensor updates via HTTP, validates a shared token stored in MySQL,
stores an event log, and keeps the latest status per room.

## Run the API (Docker)
1. Ensure Docker Desktop is running.
2. From this folder, run:

```
docker compose up --build
```

The API will be available at `http://localhost:8000`.

## Token used by sensors
The default token is seeded in `db/init.sql`:

```
INSERT IGNORE INTO api_tokens (token) VALUES ('changeme');
```

Before first run, change `changeme` to your desired token.

If the MySQL volume has already been created, update the token directly in the DB:

```
UPDATE api_tokens SET token = 'your_token' WHERE id = 1;
```

## API request
Endpoint:
- `POST /sensor/update`

Body (JSON):
```
{
  "sensor_id": "sensor-1",
  "token": "changeme",
  "room_name": "Lab",
  "state": 1
}
```

Test with curl:
```
Invoke-RestMethod -Method Post -Uri "http://192.168.1.241:8000/sensor/update" -ContentType "application/json" -Body '{"sensor_id":"sensor-1","token":"changeme","room_name":"Lab","state":1}'

curl.exe http://192.168.1.241:8000/health
```

## Connect to MySQL and query tables
The MySQL service is exposed on `localhost:3306`.

Credentials (from `docker-compose.yml`):
- User: `app_user`
- Password: `app_password`
- Database: `mmwave`

Connect using the MySQL:

docker exec -it mmwave-mysql bash
```
mysql -u app_user -p
```
app_password

Then:
```
USE mmwave;
SHOW TABLES;
SELECT * FROM api_tokens;
SELECT * FROM sensor_events ORDER BY id DESC LIMIT 10;
SELECT * FROM room_status;
```
