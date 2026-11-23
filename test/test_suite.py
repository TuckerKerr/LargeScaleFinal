import unittest
import pytest
from unittest.mock import patch
from hypothesis import given, settings, Verbosity, example
import hypothesis.strategies as st
from proj_library import collector_lib
import time
from concurrent.futures import ThreadPoolExecutor


"""
TEST 1: RETURN OF 3 EVENTS (SHOULD NEVER BE AN EMPTY EVENT DUE TO THE PROGRAM)

TEST 2: REDIS IS DOWN

TEST 3: VALID DATA EVENT

TEST 4: DATABASE RAISES EXCEPTION

TEST 5: REGISTRATION WORKS

TEST 6: MISSING USERNAME

TEST 7: AN EVENT IS FULL AND SOMEONE TRIES TO REGISTER

TEST 8: USER IS ALREADY REGISTERED

TEST 9: USER CAN REGISTER

TEST 10: RETURNS APPROPRIATE ATTENDANCE FOR AN EVENT

TEST 11: TEST THE RETURN OF DATA FROM THE DB
"""

#TEST 1
def test_get_events():
    expected = [
        {
            "event_id": 1,
            "event_name": "San Francisco 49ers Fan Watch Party",
            "capacity": 49,
            "registered_count": 0
        },
        {
            "event_id": 2,
            "event_name": "Miami Heat Fan Watch Party",
            "capacity": 30,
            "registered_count": 0
        },
        {
            "event_id": 3,
            "event_name": "WWE History Night: Ric Flair Career Discussion",
            "capacity": 16,
            "registered_count": 0
        }
    ]

    with patch(
        "proj_library.collector_lib.lib.getEvents",
        return_value=expected
    ):
        result = collector_lib.getEvents()

    assert result == expected


def test_get_single_event():
    expected = [
        {
            "event_name": "Miami Heat Fan Watch Party",
            "capacity": 30,
            "registered_count": 0
        }
    ]

    with patch(
        "proj_library.collector_lib.lib.getEvents",
        return_value=expected
    ):
        result = collector_lib.getSingleEvent(2)

    assert [result] == expected

def test_users_register():
    # Get attendance before registering
    before = collector_lib.getSingleEvent(1)
    initial_count = before["registered_count"]

    # Add registration request to Redis
    message_id = collector_lib.handleRequests({
        "username": "Avery Brooks",
        "event": 1
    })

    assert message_id is not None

    # Wait for processor to update PostgreSQL
    deadline = time.monotonic() + 10

    while time.monotonic() < deadline:
        after = collector_lib.getSingleEvent(1)

        if after["registered_count"] == initial_count + 1:
            break

        time.sleep(0.25)
    else:
        pytest.fail(f"Registration was not processed within 10 seconds. Initial Count: {initial_count}, After: {after["registered_count"]}")

    assert after["registered_count"] == initial_count + 1


def test_users_2nd_attempt():
    # Add registration request to Redis
    message_id = collector_lib.handleRequests({
        "username": "Jordan Lee",
        "event": 1
    })

    assert message_id != "Duplicate"


    second_message = collector_lib.handleRequests({
        "username": "Jordan Lee",
        "event": 1
    })

    assert second_message == "Duplicate"

# RUN A TEST TO CHECK MORE THAN CAPACITY REQUESTS RUNNING AT ONCE
def test_mass_register():
    event_id = 3
    capacity = 16
    users = [
        "Avery Brooks",
        "Jordan Lee",
        "Morgan Patel",
        "Taylor Nguyen",
        "Riley Johnson",
        "Cameron Rivera",
        "Casey Kim",
        "Jamie Thompson",
        "Alex Martinez",
        "Quinn Davis",
        "Sam Wilson",
        "Reese Brown",
        "Skyler Ahmed",
        "Parker Garcia",
        "Drew Robinson",
        "Jesse Clark",
        "Emerson Lewis",
        "Sage Walker",
        "Blair Chen",
        "Rowan Mitchell"
    ]

    before = collector_lib.getSingleEvent(event_id)

    assert before["registered_count"] == 0, (
        "Event must be empty before testing"
    )

    def register_user(username):
        return collector_lib.handleRequests({
            "username": username,
            "event": event_id
        })

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(register_user, users))

    deadline = time.monotonic() + 10

    while time.monotonic() < deadline:
        after = collector_lib.getSingleEvent(event_id)

        if after["registered_count"] == capacity:
            break

    else:
        pytest.fail(f"Expected {capacity} registration, found {after['registered_count']}")

    assert after["registered_count"] == 16