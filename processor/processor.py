import redis
from proj_library import db_lib as lib
from dotenv import load_dotenv
load_dotenv()  # reads .env and adds those pairs to os.environ

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def insertData(stream):
    last_id = "0-0"
    results = r.xread(streams={"events:raw", last_id}, count=10, block=10000,)

    for stream, events in results:
        for event_id, user in events:

            registration = lib.reserveEvent(user["username"], user["event"])
            if registration == "Event at capacity":
                return registration
            
            last_id = event_id
    return last_id, True