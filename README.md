# Concurrency-Safe Slot Booking System

> A slot reservation engine built to prevent double-bookings under concurrent load — using database-level constraints, the Repository pattern, and strict Test-Driven Development.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x-red)
![Tests](https://img.shields.io/badge/Tests-4%20Passing-brightgreen)
![TDD](https://img.shields.io/badge/Built%20With-TDD-orange)

---

## Features

- **Slot Model** — Domain entity with `start_time`, `end_time`, and `status` fields, backed by SQLAlchemy ORM
- **Enum-Enforced Status** — `AVAILABLE | HELD | BOOKED` as a Python Enum mapped to a DB Enum column — invalid states are rejected at the database level
- **Duplicate Slot Prevention** — `UniqueConstraint` on `(start_time, end_time)` enforced atomically by the DB engine, immune to race conditions
- **Repository Pattern** — Clean data access layer (`SlotRepository`) separating query logic from business rules
- **Full Test Suite (TDD)** — 4 pytest tests written *before* implementation, each driving a design decision

---

## Project Structure

```
├── models/
│   └── slot.py              # Slot model + SlotStatus enum
├── repositories/
│   └── slot_repository.py   # Data access layer (create, get_by_id)
├── tests/
│   ├── conftest.py           # pytest fixture: in-memory SQLite session
│   └── test_slot.py          # 4 tests: create, default status, persist, unique constraint
├── services/                 # (Planned: business logic layer)
└── demoDocs/                 # Architecture docs & interview prep notes
```

---

## Running Tests

```bash
# Activate virtual environment
venvCSBS\Scripts\activate

# Run all tests
pytest tests/test_slot.py -v
```

**Expected output:** `4 passed`

---

**Author:** [Ragbendra](https://github.com/ragbendra)
