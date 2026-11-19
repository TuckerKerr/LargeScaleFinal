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
            user_id INT REFERENCES users(user_id),
        );
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

