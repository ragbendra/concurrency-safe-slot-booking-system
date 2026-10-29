# Concurrency-Safe Slot Booking System

[![CI](https://github.com/ragbendra/concurrency-safe-slot-booking-system/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ragbendra/concurrency-safe-slot-booking-system/actions/workflows/ci.yml)

A small Python/SQLAlchemy project about one problem: what happens when two requests try to book the same slot at the same moment. The answer here is a MySQL row lock, and the tests are there to check that it really works.

The repository has:

- SQLAlchemy models for slots and bookings
- repository classes for the database access
- a booking service that does the whole booking in one transaction
- pytest tests that run against a real MySQL server, including ones with many threads booking at once

It's a library, not an app. There is no HTTP API, CLI or login. You run it through the tests.

## Continuous integration

GitHub Actions runs the full test suite on pull requests, on pushes to `main`, and when started manually. It uses Python 3.12 and a MySQL 8 service container. The workflow waits until MySQL is healthy, installs `requirements.txt`, then runs `python -m pytest -v`, which includes the concurrency tests. CI creates its own `slot_booking_test` database, so it needs no repository secrets.

To run the same thing locally, point the five `MYSQL_*` variables from [Setup](#setup) at a test database and run:

```powershell
python -m pytest -v
```

## Data model

There are two tables. I checked the definitions below against `SHOW CREATE TABLE` on MySQL Community Server 8.0.45.

### `slots`

| Column | Definition | Notes |
| --- | --- | --- |
| `id` | `INT`, primary key, auto-increment | Also indexed (`ix_slots_id`). |
| `start_time` | `DATETIME(6)`, not null | Keeps microseconds. |
| `end_time` | `DATETIME(6)`, not null | |
| `status` | `ENUM('AVAILABLE', 'HELD', 'BOOKED')`, not null | The default of `AVAILABLE` is set in SQLAlchemy, not in the database. |

A unique index `_start_end_uc` on `(start_time, end_time)` rejects two slots with exactly the same start and end. It does not catch overlapping slots.

### `bookings`

| Column | Definition | Notes |
| --- | --- | --- |
| `id` | `INT`, primary key, auto-increment | Also indexed (`ix_bookings_id`). |
| `user_id` | `INT`, not null | Indexed (`ix_bookings_user_id`). |
| `slot_id` | `INT`, not null, foreign key to `slots.id` | MySQL indexes it for the foreign key. It is not unique. |
| `created_at` | `DATETIME`, nullable | SQLAlchemy fills in the current UTC time as a naive value. There's no default in the database. |

I left `bookings.slot_id` non-unique on purpose. The service locks the slot row before it checks the status, and that lock is what prevents a second booking.

## How a booking works

`BookingService.book_slot` does this in one transaction:

1. Calls `SlotRepository.get_by_id(slot_id, lock=True)`.
2. The repository adds `SELECT ... FOR UPDATE`, which locks that slot's row until the transaction ends.
3. If there's no such row, it raises `SlotNotFoundException`.
4. If the locked row is already `BOOKED`, it raises `SlotAlreadyBookedException`.
5. Otherwise it inserts a `Booking`.
6. It sets the slot to `BOOKED` and commits.

With InnoDB, a second transaction asking for the same row waits for the first one to finish. When it gets the row it sees the committed `BOOKED` status and takes the already-booked path. The row lock is the only thing protecting against double bookings. The database itself doesn't enforce one booking per slot.

## Project structure

```text
.
├── models/
│   ├── __init__.py
│   ├── booking.py
│   └── slot.py
├── repositories/
│   ├── __init__.py
│   ├── booking_repository.py
│   └── slot_repository.py
├── services/
│   └── booking_service.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_booking.py
│   ├── test_concurrency.py
│   └── test_slot.py
├── .env.example
├── exceptions.py
├── LICENSE
├── README.md
└── requirements.txt
```

## Setup

I ran the full suite on Python 3.12.7. The code needs Python 3.10 or newer because it uses the newer union type syntax.

### 1. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Create a test database

The tests create the tables and drop them again when they finish, so use an empty database that is only for this project:

```sql
CREATE DATABASE slot_booking_test;
CREATE USER 'slot_booking_test'@'127.0.0.1' IDENTIFIED BY 'change_me';
GRANT ALL PRIVILEGES ON slot_booking_test.* TO 'slot_booking_test'@'127.0.0.1';
```

The fixture refuses to run if `MYSQL_DATABASE` doesn't contain `test`.

### 3. Set the connection details

Copy the example file and edit the values for your MySQL server:

```powershell
Copy-Item .env.example .env
```

| Variable | What it's for | Example |
| --- | --- | --- |
| `MYSQL_USER` | MySQL account the tests use | `slot_booking_test` |
| `MYSQL_PASSWORD` | Password for that account | `change_me` |
| `MYSQL_HOST` | MySQL host | `127.0.0.1` |
| `MYSQL_PORT` | MySQL port | `3306` |
| `MYSQL_DATABASE` | The test database | `slot_booking_test` |

## Running the tests

From the repository root:

```powershell
python -m pytest -v
```

**Careful:** the fixtures call `Base.metadata.create_all()` before each database test and `Base.metadata.drop_all()` after it. Only point them at an empty database made for testing. The "must contain `test`" check stops the obvious mistakes, but it can't tell whether a database with `test` in its name is actually safe to wipe.

| Test file | What it covers |
| --- | --- |
| `tests/test_slot.py` | Creating a slot, the `AVAILABLE` default, saving it, and rejecting an exact duplicate. |
| `tests/test_booking.py` | The `created_at` default, saving the current UTC time, a successful booking, and the service exceptions. |
| `tests/test_concurrency.py` | Many threads booking at once, then a check with a fresh session of the booking rows and the slot status. |

The full suite is 12 tests and takes a bit under a minute (55.60s and 57.94s on two runs).

## Concurrency checks

Each worker thread opens its own SQLAlchemy `Session` from the fixture's `sessionmaker`. The engine uses `NullPool`, so every worker gets its own MySQL connection instead of sharing one from a pool.

What the tests check:

- The single-slot test uses 10 threads.
- The stress test repeats that over 50 different slots, so 500 booking attempts in total.
- For each slot, exactly 1 worker books it and exactly 9 get `already_booked`.
- No worker ends in `error`. If one does, the exception text is in the assertion message.
- A fresh session finds exactly one booking row for the slot, and the slot status is `BOOKED`.

I also checked that the test can fail. With `lock=True` changed to `lock=False`, the stress test failed on the first slot. It saw only 6 `already_booked` results instead of 9, and some workers raised unexpected errors. I put `lock=True` back afterwards and the concurrency tests passed again (2 passed in 57.38s).

All of these results are from Python 3.12.7 and MySQL Community Server 8.0.45.

## Known limitations

This is a library: there's no HTTP API, CLI, login or user management.

Things it doesn't do:

- It doesn't detect overlapping slots. Only an exact same start and end is rejected, so 10:00-11:00 and 10:30-11:30 can both exist.
- Nothing but the row lock stops a double booking. `bookings.slot_id` isn't unique, so anything that writes bookings without going through the service could book a slot twice.
- `HELD` is in the status enum, but nothing sets it.
- There are no migrations. The tests create and drop the tables straight from the models.

Smaller notes: `created_at` is a naive `DATETIME`, so callers have to treat it as UTC. The concurrency tests need a real MySQL server with InnoDB-style row locks, so SQLite won't work for them. I've only run this on MySQL 8.0.45, so I can't say how it behaves on other MySQL-compatible servers.

## License

MIT. See [LICENSE](LICENSE).
