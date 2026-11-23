import redis
from proj_library import db_lib as lib
from dotenv import load_dotenv
load_dotenv()  # reads .env and adds those pairs to os.environ

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def insertData():
    last_id = "0-0"
    while True:
        results = r.xread(streams={"events:raw": last_id}, count=10, block=10000,)

        for stream_name, events in results:
            for event_id, user in events:
                username = user["username"]
                event = user["event"]
                try:
                    registration = lib.reserveEvent(username, event)

                    if registration == "Event at capacity":
                        print(f"User: {username} cant register for {event} due to capacity")

                    last_id = event_id
                except Exception as error:
                    print(f"Error processing {event_id}: {error}")
                    raise
    return last_id, True

if __name__ == "__main__":
    insertData()