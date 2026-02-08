import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, conint
import mysql.connector
from mysql.connector import Error


# Initialize the FastAPI application instance.
app = FastAPI()


# Define and validate the expected request body from sensors.
class SensorUpdate(BaseModel):
    sensor_id: str = Field(..., min_length=1, max_length=128)
    token: str = Field(..., min_length=1)
    room_name: str = Field(..., min_length=1, max_length=128)
    state: conint(ge=0, le=1)


# Define the response shape for room status data.
class RoomStatus(BaseModel):
    room_name: str
    state: conint(ge=0, le=1)
    updated_at: str
    occupied_seconds: int | None


# Load database connection settings from environment variables.
def get_db_config() -> dict:
    return {
        "host": os.getenv("MYSQL_HOST", "mysql"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "app_user"),
        "password": os.getenv("MYSQL_PASSWORD", "app_password"),
        "database": os.getenv("MYSQL_DATABASE", "mmwave"),
    }


# Open a new connection to the MySQL database.
def get_connection():
    return mysql.connector.connect(**get_db_config())


# Simple health endpoint to verify the API is running.
@app.get("/health")
def health():
    return {"status": "ok"}


# Receive sensor updates, validate token, and write data to MySQL.
@app.post("/sensor/update")
def sensor_update(payload: SensorUpdate):
    try:
        # Connect to the database and prepare a cursor.
        conn = get_connection()
        cursor = conn.cursor()

        # Verify the shared token exists in the database.
        cursor.execute(
            "SELECT COUNT(*) FROM api_tokens WHERE token = %s",
            (payload.token,),
        )
        token_count = cursor.fetchone()[0]
        if token_count == 0:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Store the event in the append-only history table.
        cursor.execute(
            """
            INSERT INTO sensor_events (sensor_id, room_name, state)
            VALUES (%s, %s, %s)
            """,
            (payload.sensor_id, payload.room_name, payload.state),
        )

        # Upsert the latest room status for quick lookup.
        cursor.execute(
            """
            INSERT INTO room_status (room_name, state)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                state = VALUES(state),
                updated_at = CURRENT_TIMESTAMP
            """,
            (payload.room_name, payload.state),
        )

        # Persist changes and respond to the caller.
        conn.commit()
        return {"status": "ok"}
    except HTTPException:
        # Bubble up explicit HTTP errors (e.g., invalid token).
        raise
    except Error:
        # Convert database errors into a generic API error response.
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        # Ensure cursor and connection are closed even on errors.
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


# Return the latest status for all rooms, including occupied duration.
@app.get("/rooms", response_model=list[RoomStatus])
def get_rooms():
    try:
        # Connect to the database and prepare a cursor that returns dicts.
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch room status and compute occupied duration in seconds.
        cursor.execute(
            """
            SELECT
                room_name,
                state,
                updated_at,
                CASE
                    WHEN state = 1 THEN TIMESTAMPDIFF(SECOND, updated_at, NOW())
                    ELSE NULL
                END AS occupied_seconds
            FROM room_status
            ORDER BY room_name
            """
        )
        rows = cursor.fetchall()

        # Normalize datetime to ISO-8601 strings for JSON output.
        for row in rows:
            if row.get("updated_at") is not None:
                row["updated_at"] = row["updated_at"].isoformat()

        return rows
    except Error:
        # Convert database errors into a generic API error response.
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        # Ensure cursor and connection are closed even on errors.
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass
