from dotenv import load_dotenv
load_dotenv()  # reads .env and adds those pairs to os.environ

import os
import psycopg
from psycopg.rows import dict_row


conn_info = psycopg.connect(
    host=os.environ["PGHOST"],
    port=int(os.environ["PGPORT"]),
    dbname=os.environ["PGDATABASE"],
    user=os.environ["PGUSER"],
    password=os.environ["PGPASSWORD"],
)

def commitQueries():
    try:
        conn_info.commit()
    except Exception:
        conn_info.rollback()
        raise
    return
    

def createTables():
    conn_info.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id BIGSERIAL PRIMARY KEY,
            event_name VARCHAR(255) NOT NULL,
            campus VARCHAR(255) NOT NULL,
            capacity INT NOT NULL,
            date TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id BIGSERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS registration(
            request_id BIGSERIAL PRIMARY KEY,
            event_id INT REFERENCES events(event_id),
            username VARCHAR(255) REFERENCES users(name),
            requested_at TIMESTAMPTZ,
            status TEXT NOT NULL CHECK (status IN ('pending', 'confirmed', 'rejected')),
            rejection_reason TEXT,
            redis_message_id TEXT UNIQUE,
            CHECK ((status = 'rejected') = (rejection_reason IS NOT NULL))
        );
    """)
    return

def createProcedures():
    conn_info.execute("""
        CREATE OR REPLACE FUNCTION check_attendance()
            RETURNS TABLE (
                event_id BIGINT,
                event_name VARCHAR(255),
                campus VARCHAR(255),
                capacity INTEGER,
                registered_count BIGINT
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RETURN QUERY
                SELECT
                    e.event_id,
                    e.event_name,
                    e.campus,
                    e.capacity,
                    COUNT(DISTINCT r.username)
                FROM events AS e
                LEFT JOIN registration AS r
                    ON r.event_id = e.event_id
                    AND r.status = 'confirmed'
                GROUP BY
                    e.event_id,
                    e.event_name,
                    e.campus,
                    e.capacity
                ORDER BY e.event_id;
            END;
            $$;

        CREATE OR REPLACE PROCEDURE check_event_attendance(
            IN p_event_id INTEGER,
            OUT event_name VARCHAR(255),
            OUT capacity INTEGER,
            OUT registered_count BIGINT
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            SELECT
                e.event_name,
                e.capacity,
                COUNT(DISTINCT r.username)
            INTO
                event_name,
                capacity,
                registered_count
            FROM events AS e
            LEFT JOIN registration AS r
                ON r.event_id = e.event_id
                AND r.status = 'confirmed'
            WHERE e.event_id = p_event_id
            GROUP BY e.event_id, e.event_name, e.capacity;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Event ID % does not exist', p_event_id;
            END IF;
        END;
        $$;

        CREATE OR REPLACE PROCEDURE save_registration(
            p_event_id INT,
            p_username VARCHAR,
            p_requested_at TIMESTAMPTZ,
            p_status TEXT,
            p_rejection_reason TEXT,
            p_redis_message_id TEXT
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            INSERT INTO registration (
                event_id, username, requested_at, status,
                rejection_reason, redis_message_id
            ) VALUES (
                p_event_id, p_username, p_requested_at, p_status,
                p_rejection_reason, p_redis_message_id
            );
        END;
        $$;
    """)
    return

def insertEvents():
    conn_info.execute("""
        INSERT INTO events(event_name, campus, capacity, date) VALUES
            ('San Francisco 49ers Fan Watch Party', 'North Campus', 49, '2026-12-06 16:25:00-05:00'),
            ('Miami Heat Fan Watch Party', 'South Campus', 30, '2026-12-09 19:30:00-05:00'),
            ('WWE History Night: Ric Flair Career Discussion', 'North Campus', 16, '2026-12-11 18:00:00-05:00');

    """)
    return

def insertUsers():
    conn_info.execute("""
        INSERT INTO users (name) VALUES
            ('Avery Brooks'),
            ('Jordan Lee'),
            ('Morgan Patel'),
            ('Taylor Nguyen'),
            ('Riley Johnson'),
            ('Cameron Rivera'),
            ('Casey Kim'),
            ('Jamie Thompson'),
            ('Alex Martinez'),
            ('Quinn Davis'),
            ('Sam Wilson'),
            ('Reese Brown'),
            ('Skyler Ahmed'),
            ('Parker Garcia'),
            ('Drew Robinson'),
            ('Jesse Clark'),
            ('Emerson Lewis'),
            ('Sage Walker'),
            ('Blair Chen'),
            ('Rowan Mitchell');    
    """)
    return

def reserveEvent(username, event, requested_at=None, message_id=None):
    with conn_info.transaction(), conn_info.cursor() as cursor:

        cursor.execute("""
            SELECT event_id FROM events WHERE event_id = %s FOR UPDATE
        """, (event,))
        if cursor.fetchone() is None:
            raise ValueError(f"Event {event} does not exist")

        if message_id is not None:
            cursor.execute(
                """
                SELECT status, rejection_reason
                FROM registration
                WHERE redis_message_id = %s
                """,
                (message_id,),
            )
            existing = cursor.fetchone()
            if existing is not None:
                return {
                    "status": existing[0],
                    "rejection_reason": existing[1],
                }
        cursor.execute("CALL check_event_attendance(%s, NULL, NULL, NULL)", (event,),)
        __, capacity, registered_count = cursor.fetchone()

        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM registration
                WHERE event_id = %s
                  AND username = %s
                  AND status = 'confirmed'
            )
            """,
            (event, username),
        )
        registered = cursor.fetchone()[0]
        rejection_reason = None
        if registered:
            rejection_reason = "already_reserved"
        elif registered_count >= capacity:
            rejection_reason = "event_full"
        
        status = "rejected" if rejection_reason else "confirmed"

        cursor.execute("""
            CALL save_registration(%s, %s, %s, %s, %s, %s)
        """, (event, username, requested_at, status, rejection_reason, message_id))
        return {"status": status, "rejection_reason": rejection_reason}

def getEvents():
    with conn_info.cursor(row_factory=dict_row) as cursor:
        cursor.execute("SELECT * FROM check_attendance()")
        return cursor.fetchall()

def getEventsForAttendee(username):
    with conn_info.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            """
            SELECT e.*, EXISTS (
                SELECT 1
                FROM registration AS r
                WHERE r.event_id = e.event_id
                  AND r.username = %s
                  AND r.status = 'confirmed'
            ) AS already_registered
            FROM check_attendance() AS e
            ORDER BY e.event_id
            """,
            (username,),
        )
        return cursor.fetchall()


def getSingleEvent(event):
    with conn_info.cursor(row_factory=dict_row) as cursor:
        cursor.execute("CALL check_event_attendance(%s, NULL, NULL, NULL)", (event,))
        return cursor.fetchone()
        
def getReservationOutcome(message_id):
    with conn_info.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            """
            SELECT status, rejection_reason, requested_at FROM registration
            WHERE redis_message_id = %s
            """,
            (message_id,),
        )
        return cursor.fetchone()

def getUser(username):
    with conn_info.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            """
            SELECT user_id FROM users WHERE name = %s
            """,
            (username,),
        )
        response = cursor.fetchone()
        if response is None:
            return "No User Exists"
        else:   
            return response