from dotenv import load_dotenv
load_dotenv()  # reads .env and adds those pairs to os.environ

import os
import psycopg
from proj_library import db_lib as lib
from proj_library import processor_lib as pl


conn_info = psycopg.connect(
    host=os.environ["PGHOST"],
    port=int(os.environ["PGPORT"]),
    dbname=os.environ["PGDATABASE"],
    user=os.environ["PGUSER"],
    password=os.environ["PGPASSWORD"],
)

def initializeSchema():
    # RUN QUERIES TO CREATE THE TABLES IF THEY ARE NOT PRESENT
    lib.createTables()
    lib.insertEvents()
    lib.insertUsers()
    lib.commitQueries()
    return