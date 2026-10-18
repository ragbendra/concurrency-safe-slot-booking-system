# Concurrency-Safe Slot Booking System

This repository is a Python library-style backend example with SQLAlchemy models, repositories, and a booking service. It demonstrates preventing two concurrent bookings of the same slot with a MySQL row lock. It has no HTTP API and no CLI; the code is exercised through its pytest tests.

## Data model

The ORM defines two tables:

- `slots`: `id` (integer primary key), `start_time` (`DATETIME(6)`), `end_time` (`DATETIME(6)`), and `status` (non-null MySQL `ENUM` with `AVAILABLE`, `HELD`, and `BOOKED`). `id`, `start_time`, and `end_time` are non-null through the primary-key or column declarations. `status` has the SQLAlchemy-side default `AVAILABLE`.
- `bookings`: `id` (integer primary key), `user_id` (non-null integer with an index), `slot_id` (non-null integer foreign key to `slots.id`), and `created_at` (naive `DateTime`). The timestamp default is a callable that stores the current UTC time as a naive UTC value.

`slots` has a unique constraint named `_start_end_uc` on `(start_time, end_time)`. It prevents exact duplicate slots, not overlapping time ranges. `HELD` is defined in the enum but is not set by the current code.

`SHOW CREATE TABLE` was verified on the configured MySQL database. Both tables use InnoDB. The `slots` table has the primary key, `_start_end_uc`, and the generated `ix_slots_id` index. The `bookings` table has the foreign key to `slots.id`, indexes for `slot_id`, `user_id`, and `id`, and no unique constraint on `slot_id`. The database DDL has no server-side default for `status` or `created_at`; those defaults are applied by SQLAlchemy, and `created_at` is nullable in the current model.

## How double-booking is prevented

`BookingService.book_slot`:

1. Loads the requested slot through `SlotRepository.get_by_id(..., lock=True)`, which uses `SELECT ... FOR UPDATE`.
2. Raises `SlotNotFoundException` if the slot does not exist.
3. Re-checks the locked row and raises `SlotAlreadyBookedException` if its status is `BOOKED`.
4. Inserts a `Booking`, sets the slot status to `BOOKED`, and commits the transaction.

When two transactions request the same slot, the second transaction waits for the row lock and then observes the committed `BOOKED` status. The row lock is the only double-booking guard: there is no unique constraint on `bookings.slot_id`.

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

The full MySQL-backed suite was verified with Python 3.12.7. Python 3.14.0 was also used for dependency and model checks. Python 3.10 or newer is required by the type annotations in the code.

Create a virtual environment and install the pinned dependencies:

```text
python -m venv .venv
```

On Windows PowerShell:

```text
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create an empty, dedicated MySQL test database. The database name must contain `test`; for example:

```sql
CREATE DATABASE slot_booking_test;
CREATE USER 'slot_booking_test'@'127.0.0.1' IDENTIFIED BY 'change_me';
GRANT ALL PRIVILEGES ON slot_booking_test.* TO 'slot_booking_test'@'127.0.0.1';
```

Copy the example configuration and edit the values for your server:

```text
cp .env.example .env
```

On PowerShell, the equivalent command is `Copy-Item .env.example .env`. The example contains `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST`, `MYSQL_PORT`, and `MYSQL_DATABASE`.

## Running the tests

From the repository root, run:

```text
python -m pytest -v
```

**Warning:** the test fixtures create all tables in the configured database and drop them afterwards. Use a dedicated empty database. The fixture refuses database names that do not contain `test`.

The latest full-suite run reported `12 passed in 55.60s`.

| Test file | Coverage |
| --- | --- |
| `tests/test_slot.py` | Slot construction, the available status default, persistence, and the exact-duplicate constraint. |
| `tests/test_booking.py` | Callable timestamp default, current UTC timestamp persistence, booking, and not-found/already-booked exceptions. |
| `tests/test_concurrency.py` | Concurrent booking categories and database state for one slot and for the repeated stress case. |

## Concurrency tests

Each worker creates its own `Session` from the fixture's `sessionmaker`. The engine uses `NullPool`, so worker sessions do not share pooled MySQL connections. The single-slot test starts 10 threads. The stress test repeats the same 10-thread attempt for 50 different slots, for 500 total attempts.

Each worker returns one of `booked`, `already_booked`, or `error`. The tests require exactly 1 `booked`, exactly 9 `already_booked`, and 0 `error` results. A fresh session then verifies one `bookings` row for the slot and a `BOOKED` slot status.

The full suite was run on Python 3.12.7 with MySQL Community Server 8.0.45:

- `pytest tests/ -v`: `12 passed in 57.94s`.
- `pytest tests/test_concurrency.py -v`: both concurrency tests passed in `53.90s`.
- `pytest tests/test_concurrency.py::test_concurrency_stress -v`: the stress test passed in `48.15s`.
- `pytest tests/ -v -s`: `12 passed in 55.60s`.

The concurrency tests therefore passed repeatedly with no worker errors. The mutation check was also completed: changing `lock=True` to `lock=False` caused `test_concurrency_stress` to fail at iteration 0 because only 6 workers were categorized as `already_booked` instead of 9, with unexpected worker errors. The code was restored to `lock=True` afterward.

## Known limitations

- There is no HTTP layer or CLI.
- The unique constraint catches exact duplicate slots only.
- Overlapping slots are not detected.
- `HELD` is defined but unused.
- The row lock is the sole guard against double-booking; `bookings.slot_id` is not unique.
- The concurrency tests require a real MySQL-compatible server with row-lock behavior; SQLite is not a substitute for these tests.
- The documented concurrency results were produced on MySQL Community Server 8.0.45; other MySQL-compatible servers may behave differently.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
