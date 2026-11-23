from dotenv import load_dotenv
load_dotenv()  # reads .env and adds those pairs to os.environ

import os
import psycopg

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
        CREATE TABLE IF NOT EXIST events (
            event_id INT BIGSERIAL PRIMARY KEY,
            event_name VARCHAR(255) NOT NULL,
            campus VARCHAR(255) NOT NULL,
            capacity INT NOT NULL,
            date TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXIST users (
            user_id INT BIGSERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
        );

        CREATE TABLE IF NOT EXIST registration(
            event_id INT REFERENCES events(event_id),
            username VARCHAR(255) REFERENCES users(name),
        );
    """)

    
    commitQueries()
    return

def createProcedures():
    conn_info.execute("""
        CREATE OR REPLACE FUNCTION check_attendance()
            RETURNS TABLE (
                event_id INTEGER,
                event_name VARCHAR(255),
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
                    e.capacity,
                    COUNT(DISTINCT r.username)
                FROM events AS e
                LEFT JOIN registration AS r
                    ON r.event_id = e.event_id
                GROUP BY
                    e.event_id,
                    e.event_name,
                    e.capacity;
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
            WHERE e.event_id = p_event_id
            GROUP BY e.event_id, e.event_name, e.capacity;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Event ID % does not exist', p_event_id;
            END IF;
        END;
        $$;

        CREATE OR REPLACE PROCEDURE save_registration(
            p_event_id INT,
            p_username VARCHAR
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM registration
                WHERE event_id = p_event_id AND username = p_username
            ) THEN
                RAISE EXCEPTION 'User % is already registered for event %',
                p_username, p_event_id;
            ELSE
                INSERT INTO registration (
                    event_id, 
                    username
                ) VALUES (
                    p_event_id,
                    p_username 
                );
            END IF;
        END;
        $$;
    """)

    commitQueries()
    return

def insertEvents():
    conn_info.execute("""
        INSERT INTO events(event_name, campus, capacity, date) VALUES
            ('San Francisco 49ers Fan Watch Party', 'North Campus', 49, '2026-12-06 16:25:00-05:00'),
            ('Miami Heat Fan Watch Party', 'South Campus', 30, '2026-12-09 19:30:00-05:00'),
            ('WWE History Night: Ric Flair Career Discussion', 'North Campus', 16, '2026-12-11 18:00:00-05:00');

    """)

    commitQueries()
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

    commitQueries()
    return

def reserveEvent(username, event):
    with conn_info.cursor() as cursor:

        cursor.execute("""
            CALL check_event_attendance(
                %s, NULL, NULL, NULL
            )
        """, (event,))

        event_attendance = cursor.fetchone()

        event_name = event_attendance[0]
        capacity = event_attendance[1]
        registered_count = event_attendance[2]

        if registered_count >= capacity:
            return "Event at capacity"
        else:
            cursor.execute("""
                CALL save_registration(%s, %s)
            """, (event, username))
            commitQueries()
            return "Registration successful"

def getEvents():
    conn_info.execute("""
        SELECT * FROM check_attendance()
    """)
    return
