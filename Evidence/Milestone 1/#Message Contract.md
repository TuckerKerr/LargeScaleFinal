# Message Contract

## Client -> API

The browser lists events with `GET /api/events`. That request has no body.

| Field | Data | Description | Needed |
| --- | --- | --- | --- |
| `eventId` | JSON integer | Event to reserve. The API converts it with `int()` and requires a value above zero. | Yes, in the `POST /api/reservations` body |
| `username` | JSON string | Fictional attendee name. Must contain a non-whitespace character. | Yes, in the POST body |
| `request_id` | Path string | Redis entry ID from the POST response. Must contain two unsigned 64-bit decimal numbers separated by a hyphen. | Yes, for `GET /api/reservations/<request_id>` |

## API -> Client

### Event list — HTTP 200 from `GET /api/events`

| Field | Data | Description | Needed |
| --- | --- | --- | --- |
| `event_id` | JSON integer | Unique event ID | Yes |
| `event_name` | JSON string | Event name | Yes |
| `campus` | JSON string | Campus where the event is held | Yes |
| `capacity` | JSON integer | Maximum confirmed attendees | Yes |
| `registered_count` | JSON integer | Number of distinct confirmed attendees | Yes |

### Reservation submission and status lookup

| Field | Data | Description | Needed |
| --- | --- | --- | --- |
| `requestId` | JSON string | Redis stream entry ID used to look up a submission | Yes on POST 202 and GET 200 |
| `status` | JSON string | `pending`, `confirmed`, `rejected`, or `unavailable`, depending on the response | Yes on POST 202/400/409/503 and GET 200/503 |
| `requested_at` | ISO 8601 string or null | Time the API received and validated the submission. Older entries can return null. | Yes on POST 202/409/503 and GET 200 |
| `rejection_reason` | JSON string or null | Reason code on rejection. Null for pending or confirmed responses that include this field. | Yes on POST 202/400/409 and GET 200 |
| `message` | JSON string | Human-readable queue acknowledgment | Yes on POST 202 |
| `error` | JSON string | Human-readable error description | Yes on error responses |

| Response | Data | Description | Needed |
| --- | --- | --- | --- |
| POST 202 | `pending` | Redis queued the request. The seat decision is still pending. | When queued |
| POST 400 | `rejected` | Invalid input. Reason is `invalid_json`, `missing_username`, or `invalid_event_id`. | When request validation fails |
| POST 409 | `rejected` | Reason is `duplicate_request`. Redis already has the attendee/event key. | When the submission is a duplicate |
| GET 200 | `pending`, `confirmed`, or `rejected` | The request was found. A saved rejection can be `already_reserved` or `event_full`. | When the request ID resolves |
| GET 400 or 404 | `error` | Invalid request ID format or no matching request | When the status lookup cannot resolve the ID |
| POST or status GET 503 | `unavailable` | The API could not complete the operation | When submission or status lookup raises an exception |
| Event list GET 500 | `error` | The API could not retrieve events | When the event query raises an exception |

## API -> Redis

The collector checks `registrations:queued` with `SADD` before appending to the `events:raw` stream with `XADD`.

| Field | Data | Description | Needed |
| --- | --- | --- | --- |
| Attendee/event key | String, `<event>:<username>` | Redis set member used to detect repeated submissions | Yes, for the duplicate check |
| `event` | Integer, serialized as a string | Event ID from the client's `eventId` | Yes |
| `username` | String | Fictional attendee name | Yes |
| `requested_at` | ISO 8601 string | Original submission timestamp. The collector supplies one for direct calls that omit it. | Yes, written for new entries |
| `status` | String | Initial stream status, `pending` | Yes, written for new entries |

`SADD` and `XADD` are separate operations. If the set write succeeds and the stream write fails, the duplicate key can remain without a queued request.

## Redis -> Processor

| Field | Data | Description | Needed |
| --- | --- | --- | --- |
| `message_id` | String | Entry ID supplied by Redis outside the payload | Yes |
| `event` | Numeric string | Event ID to look up in PostgreSQL | Yes |
| `username` | String | Attendee to check and register | Yes |
| `requested_at` | ISO 8601 string | Original submission timestamp | Optional for older stream entries |
| `status` | String | Stored as `pending` in Redis. The processor computes the outcome. | Included in new entries |

The processor uses blocking `XREAD` with an in-memory cursor. It starts at `0-0` after a restart, so retained entries can be replayed. It does not use a consumer group or explicit acknowledgment.

## Processor -> Database

The processor calls `reserveEvent()`. That function locks the event row, checks for a saved result by Redis ID, checks attendance, then calls `save_registration()` to write a new outcome.

| Field | Data | Description | Needed |
| --- | --- | --- | --- |
| `p_event_id` | SQL integer | Event being reserved | Yes |
| `p_username` | SQL varchar | Attendee name referencing `users.name` | Yes |
| `p_requested_at` | SQL timestamptz | Original submission timestamp | Yes for new requests, nullable for older requests |
| `p_status` | SQL text | Final result, `confirmed` or `rejected` | Yes |
| `p_rejection_reason` | SQL text or null | `already_reserved` or `event_full` for a rejection. Null for a confirmation. | Yes for rejections |
| `p_redis_message_id` | SQL text | Saved as `registration.redis_message_id` for status lookup and replay detection | Yes for queued requests |

Only confirmed rows count toward capacity. Unknown events or attendees can fail during processing without producing a saved rejection.

## Database -> Processor

These fields are returned by the Python database function after saving a new outcome or finding an existing one.

| Field | Data | Description | Needed |
| --- | --- | --- | --- |
| `status` | Python string | Final outcome, `confirmed` or `rejected` | Yes |
| `rejection_reason` | Python string or `None` | Reason for rejection, or `None` on confirmation | Yes, nullable |

## Database / Redis -> API

The processor saves the result in PostgreSQL. The API looks up that result by Redis entry ID. It checks Redis for the original entry when PostgreSQL has no saved result.

| Field | Data | Description | Needed |
| --- | --- | --- | --- |
| `redis_message_id` | SQL text | Lookup key matching `requestId` | Yes, for the PostgreSQL lookup |
| `status` | SQL text | Saved final status from PostgreSQL. The API returns `pending` if it finds only a Redis entry. | Yes, when found |
| `rejection_reason` | SQL text or null | Saved reason for a rejected request | Yes in final results, nullable |
| `requested_at` | SQL timestamptz or Redis string | Timestamp returned by the status endpoint as an ISO 8601 string or null | Yes in successful lookup responses, nullable |

The browser currently displays the queued state and retains `requestId` in memory. The status endpoint is available for direct calls. The browser does not yet poll it.

## Trace One Request

| Field | Data | Description | Needed |
| --- | --- | --- | --- |
| `requestId` | String | Start with the ID returned in the POST 202 response | Yes |
| Redis entry ID | String | Find the entry with `XRANGE events:raw <id> <id>` | Yes |
| Processor `request_id` | String | Match the same ID against processor output for the timestamp, status, and reason | Yes |
| `registration.redis_message_id` | SQL text | Match the same ID against the PostgreSQL row. The numeric `registration.request_id` is a separate primary key. | Yes |

```sql
SELECT request_id, redis_message_id, event_id, username,
       requested_at, status, rejection_reason
FROM registration
WHERE redis_message_id = '<id>';
```

Implementation references are `html/collectorAPI.py`, `html/index.html`, `proj_library/src/proj_library/collector_lib.py`, `processor/processor.py`, and `proj_library/src/proj_library/db_lib.py`.
