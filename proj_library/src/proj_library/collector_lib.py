import redis
from proj_library import db_lib as lib
from dotenv import load_dotenv
load_dotenv()  # reads .env and adds those pairs to os.environ


def getEvents():
    #GET THE EVENTS AND THEIR CURRENT CAPACITIES
    return lib.getEvents()

def getSingleEvent(event):
    #GET THE EVENTS AND THEIR CURRENT CAPACITIES
    return lib.getSingleEvent(event)

def handleRequests(userEvent):
    #EACH USER CLICK RUNS THIS, TAKES THEIR USERNAME AND EVENT NUMBER, AND THEN ADDS THEM TO THE STREAM
    stream = redis.Redis(host='localhost', port=6379, decode_responses=True)
    username = str(userEvent["username"])
    event = int(userEvent["event"])
    unique_key = f"{event}:{username}"

    added = stream.sadd("registrations:queued", unique_key)

    if added == 1:
        message_id = stream.xadd("events:raw", {
            "username": username,
            "event": event
            })
        return message_id
    else:
       return "Duplicate"

def readStream():
    stream = redis.Redis(host='localhost', port=6379, decode_responses=True)
    first_user = stream.xrange("events:raw", count=1)
    latest_user = stream.xrevrange("events:raw", count=1)
    print("\nFirst User: ", first_user)
    print("\nLatest User: ", latest_user)