# Message Contract

Client -> API

| Field | Data | Description | Needed |
|-------|------|-------------|--------|
| event_id | int | the API needs to know what the events ID is to pass back so a user can register for an event | yes |
|-------|------|-------------|--------|
| username | varchar | the API needs to know who is going to an event | yes |
|-------|------|-------------|--------|

API -> Client

| Field | Data | Description | Needed |
|-------|------|-------------|--------|
| event_id | int | event unique key | yes |
|-------|------|-------------|--------|
| event_name | varchar | name of the event | yes |
|-------|------|-------------|--------|
| capacity | int | how many people max can go | yes |
|-------|------|-------------|--------|
| registered_count | int | how many people are going | yes |
|-------|------|-------------|--------|


API -> Redis

| Field | Data | Description | Needed |
|-------|------|-------------|--------|
| event_id | int | event unique key | yes |
|-------|------|-------------|--------|
| username | varchar | who is going to the event | yes |
|-------|------|-------------|--------|


Redis -> Processor

| Field | Data | Description | Needed |
|-------|------|-------------|--------|
| event_id | int | the API needs to know what the events ID is to pass back so a user can register for an event | yes |
|-------|------|-------------|--------|
| username | varchar | the API needs to know who is going to an event | yes |
|-------|------|-------------|--------|


Processor -> Database

| Field | Data | Description | Needed |
|-------|------|-------------|--------|
| event_id | int | the API needs to know what the events ID is to pass back so a user can register for an event | yes |
|-------|------|-------------|--------|
| username | varchar | the API needs to know who is going to an event | yes |
|-------|------|-------------|--------|


Database -> Processor

| Field | Data | Description | Needed |
|-------|------|-------------|--------|
| event_id | int | the API needs to know what the events ID is to pass back so a user can register for an event | yes |
|-------|------|-------------|--------|
| username | varchar | the API needs to know who is going to an event | yes |
|-------|------|-------------|--------|


Processor -> API

| Field | Data | Description | Needed |
|-------|------|-------------|--------|
| event_id | int | the API needs to know what the events ID is to pass back so a user can register for an event | yes |
|-------|------|-------------|--------|
| username | varchar | the API needs to know who is going to an event | yes |
|-------|------|-------------|--------|


Required fields and data types.



Identifiers.



Validation rules.



Status meanings.



How related logs can be connected to a single request.