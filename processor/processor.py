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
            for message_id, user in events:
                username = user["username"]
                event = user["event"]
                requested_at = user.get("requested_at")
                try:
                    outcome = lib.reserveEvent(username, event, requested_at, message_id)
                    status = outcome["status"]
                    rejection_reason = outcome["rejection_reason"]
                    if rejection_reason == "event_full":
                        print(f"User: {username} cant register for {event} due to capacity")

                    print(
                        f"request_id={message_id} requested_at={requested_at} "
                        f"status={status} rejection_reason={rejection_reason}"
                    )
                    last_id = message_id
                except Exception as error:
                    print(
                        f"Error processing {message_id}: {error} "
                        f"requested_at={requested_at} status=unavailable"
                    )
                    raise
    return last_id, True

if __name__ == "__main__":
    insertData()