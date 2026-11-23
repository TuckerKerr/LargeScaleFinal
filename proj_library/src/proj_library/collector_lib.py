import redis
from proj_library import db_lib as lib
from dotenv import load_dotenv
load_dotenv()  # reads .env and adds those pairs to os.environ


def createStream():
    stream = redis.Redis(host='localhost', port=6379, decode_responses=True)
    return stream

def getEvents():
    #GET THE EVENTS AND THEIR CURRENT CAPACITIES
    lib.getEvents()
    return

def handleRequests(userEvent):
    #TAKE THE REQUESTS, ADD THEM TO THE STREAM, THEN SEND THEM TO THE PROCESSOR
    # EACH USER CLICK RUNS THIS, TAKES THEIR USERNAME AND EVENT NUMBER, AND THEN ADDS THEM TO THE STREAM
    stream = createStream()
    stream.xadd("events:raw", userEvent)
    # SEND DATA TO THE BACKEND
    return

def readStream():
    stream = createStream()
    first_user = stream.xrange("events:raw", count=1)
    latest_user = stream.xrevrange("events:raw", count=1)
    print("\nFirst User: ", first_user)
    print("\nLatest User: ", latest_user)