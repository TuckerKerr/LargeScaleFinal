# LargeScaleFinal
This is my Large Scale Distributed Systems Final where we have to create and set up an event registration system. Following this will be the commands you need in order to recreate and run the system 

## Environment Recreation
In order to run the project you will want to set up your environment and make sure all the dependencies are set up. 

To install them, you simply have to set up the environment and install the library I have built
```bash
py -3.13 -m venve .venv
.\.venve\Scripts\Activate.ps1
py -3.13 -m pip install flask 'psycopg[binary]' redis python-dotenv pytest hypothesis
py -3.13 -m pip install -e ./proj_library/
```
If you are having troubles with your terminal allowing activation, run

```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

## Docker
You will then want to set up your docker containers

```bash
docker compose config --services
docker compose up -d
docker compose ps
```

## Database
Before you begin, you will need to set up your own .env file holding your database credentials to then get the actual database set up
```bash
PGHOST=test
PGPORT=1234
PGDATABASE=test
PGUSER=test
PGPASSWORD=test
POSTGRES_PASSWORD=test
```
From there, make sure your credentials are aligned and then you should be able to run 

```bash
py -3.13 -c "import db_connect; db_connect.initializeSchema()"
```
This should set your environment up with all of the data you need such as the tables, procedures and functions, and dummy data

## Running Application
You will need 3 terminals to continue working from here on out. one for your application/API, one for the processor, and the final one for you to run commands in.

### Terminal 1 - API
Running the follow commands will allow for the Flask API to listen in on your device via port 5000 where all data will pass through
```bash
.\.venv\Scripts\Activate.ps1
py -3.13 html/collectorAPI.py
```

### Terminal 2 - Processor
Running this command will turn on the processor which will listen to the redis stream for any new entries to the stream and process them to put into the database
```bash
.\.venv\Scripts\Activate.ps1
py -3.13 processor/processor.py
```

### Terminal 3
To run the program you can either load the webpage at 
```bash
https://127.0.0.1:5000/
```

or if you do not want to see visually, you can also run the test suite which will take care of all of the data implementation and run the different types of tests that are needed to make sure everything runs smoothly and correctly
```bash
py -3.13 -m pytest test/test_suite.py
```