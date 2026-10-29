# Concurrency-Safe Slot Booking System

[![CI](https://github.com/ragbendra/concurrency-safe-slot-booking-system/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ragbendra/concurrency-safe-slot-booking-system/actions/workflows/ci.yml)

A focused Python/SQLAlchemy backend that demonstrates how a MySQL row lock can protect a single slot from concurrent double-booking.

This repository contains:

- SQLAlchemy models for slots and bookings.
- Repository classes for persistence operations.
- A service-layer booking transaction.
- MySQL-backed pytest tests, including concurrent worker tests.

It is intentionally library-style: there is no HTTP API, CLI, authentication layer, or web application. The behavior is exercised through the test suite.

## Continuous integration

GitHub Actions runs the full test suite on pull requests, pushes to `main`, and manual workflow runs. The workflow uses Python 3.12 and a MySQL 8 service container; it waits for MySQL to become healthy before installing `requirements.txt` and running `python -m pytest -v`. This includes the MySQL row-lock concurrency tests. CI creates a dedicated `slot_booking_test` database and does not require repository secrets.

To run the same suite locally, configure the five `MYSQL_*` variables described in [Setup](#setup) to point to a dedicated MySQL test database, then run:

```powershell
python -m pytest -v
```

## Data model

The ORM defines two tables. The definitions below were checked against `SHOW CREATE TABLE` on MySQL Community Server 8.0.45.

### `slots`

| Column | Definition | Notes |
| --- | --- | --- |
| `id` | `INT`, primary key, auto-increment | SQLAlchemy also declares an index; MySQL creates `ix_slots_id`. |
| `start_time` | `DATETIME(6)`, not null | Microsecond precision is preserved. |
| `end_time` | `DATETIME(6)`, not null | Must be paired with `start_time`. |
| `status` | MySQL `ENUM('AVAILABLE', 'HELD', 'BOOKED')`, not null | SQLAlchemy-side default: `AVAILABLE`; no server-side default. |

Constraint: `_start_end_uc` uniquely indexes `(start_time, end_time)`. It prevents exact duplicate slots, not overlapping time ranges. `HELD` is defined but no current code path sets it.

### `bookings`

| Column | Definition | Notes |
| --- | --- | --- |
| `id` | `INT`, primary key, auto-increment | SQLAlchemy also declares `ix_bookings_id`. |
| `user_id` | `INT`, not null | Indexed as `ix_bookings_user_id`. |
| `slot_id` | `INT`, not null, foreign key to `slots.id` | MySQL creates an index for the foreign key. It is not unique. |
| `created_at` | `DATETIME`, nullable | SQLAlchemy supplies a callable default containing the current UTC time as a naive UTC value; there is no server-side default. |

There is deliberately no unique constraint on `bookings.slot_id`. The booking transaction relies on locking the corresponding row in `slots` before checking and changing its status.

## How booking prevents double-booking

`BookingService.book_slot` performs the following transaction:

1. Calls `SlotRepository.get_by_id(slot_id, lock=True)`.
2. The repository adds `SELECT ... FOR UPDATE`, locking the matching slot row for the current transaction.
3. Raises `SlotNotFoundException` when no row exists.
4. Checks the locked status and raises `SlotAlreadyBookedException` when it is already `BOOKED`.
5. Inserts a `Booking`.
6. Changes the slot status to `BOOKED` and commits.

With InnoDB, a concurrent transaction requesting the same row waits for the first transaction to release its lock. It then reads the committed `BOOKED` status and takes the expected already-booked path. The row lock is the sole protection against duplicate bookings; the database does not enforce uniqueness on `bookings.slot_id`.

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

The full MySQL-backed suite was verified with Python 3.12.7. The code requires Python 3.10 or newer because it uses modern union type annotations.

### 1. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Create a dedicated test database

The tests create tables and drop them during fixture teardown. Use an empty database dedicated to this test project:

```sql
CREATE DATABASE slot_booking_test;
CREATE USER 'slot_booking_test'@'127.0.0.1' IDENTIFIED BY 'change_me';
GRANT ALL PRIVILEGES ON slot_booking_test.* TO 'slot_booking_test'@'127.0.0.1';
```

The fixture refuses to run when `MYSQL_DATABASE` does not contain `test`.

### 3. Configure the connection

Copy the example file and edit the values for the local MySQL server:

```powershell
Copy-Item .env.example .env
```

`.env.example` documents these variables:

| Variable | Purpose | Example |
| --- | --- | --- |
| `MYSQL_USER` | MySQL account used by the tests | `slot_booking_test` |
| `MYSQL_PASSWORD` | Password for that account | `change_me` |
| `MYSQL_HOST` | MySQL host | `127.0.0.1` |
| `MYSQL_PORT` | MySQL port | `3306` |
| `MYSQL_DATABASE` | Dedicated test database | `slot_booking_test` |


## Running the tests

From the repository root:

```powershell
python -m pytest -v
```

**Safety warning:** the fixtures call `Base.metadata.create_all()` before each database-backed test and `Base.metadata.drop_all()` afterward. Point the environment variables at a dedicated empty database. The database-name guard prevents accidental use of names that do not contain `test`, but it cannot identify every unsafe database name.

| Test file | Coverage |
| --- | --- |
| `tests/test_slot.py` | Slot construction, the `AVAILABLE` default, persistence, and exact-duplicate rejection. |
| `tests/test_booking.py` | Callable timestamp default, current UTC timestamp persistence, successful booking, and service exceptions. |
| `tests/test_concurrency.py` | Concurrent result categories plus fresh-session verification of booking rows and slot status. |

Full-suite result: `12 passed in 55.60s`.

## Concurrency verification

Each worker creates an independent SQLAlchemy `Session` from the fixture's `sessionmaker`. The engine uses `NullPool`, so worker sessions obtain independent MySQL connections rather than sharing a pooled connection.

The tests verify:

- The single-slot case uses 10 worker threads.
- The stress case repeats the 10-thread case across 50 different slots, for 500 booking attempts.
- Exactly 1 worker returns `booked`.
- Exactly 9 workers return `already_booked`.
- 0 workers return `error`; unexpected exception text is included in the assertion message.
- A fresh session sees exactly one booking row for the slot.
- A fresh session sees the slot status as `BOOKED`.

The verified environment was Python 3.12.7 with MySQL Community Server 8.0.45:

| Command | Result |
| --- | --- |
| `pytest tests/ -v` | `12 passed in 57.94s` |
| `pytest tests/test_concurrency.py -v` | Both concurrency tests passed in `53.90s`. |
| `pytest tests/test_concurrency.py::test_concurrency_stress -v` | Stress test passed in `48.15s`. |
| `pytest tests/ -v -s` | `12 passed in 55.60s`. |
| `pytest tests/test_concurrency.py -q` after restoring the lock | `2 passed in 57.38s`. |

The mutation check supports the test's purpose: changing `lock=True` to `lock=False` caused the stress test to fail at iteration 0. It observed only 6 `already_booked` results instead of 9, with unexpected worker errors. The service was restored to `lock=True` afterward.

## Known limitations

- There is no HTTP API, CLI, authentication, or user-management layer.
- Overlapping slots are not detected; only exact duplicate `(start_time, end_time)` pairs are rejected.
- `HELD` is defined in the enum but is currently unused.
- The row lock is the sole double-booking guard; `bookings.slot_id` is not unique.
- There is no migration workflow. Tests create and drop tables directly with SQLAlchemy metadata.
- The concurrency tests require a real MySQL-compatible server with transactional row-lock behavior; SQLite is not a substitute for these tests.
- `created_at` is stored as naive UTC because the database column is a naive `DATETIME`; callers must interpret it as UTC.
- The documented concurrency results were produced on MySQL Community Server 8.0.45. Results may differ on other MySQL-compatible servers.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
