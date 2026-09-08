"""Shared pytest configuration (W8).

Strategy:
- Fast unit/structural tests run on SQLite (per-module engines) as before.
- Shared, reusable helpers live in ``tests/helpers.py`` (token minting, bearer
  headers) and are imported explicitly by test modules.
- PostgreSQL-gated tests are opt-in via AGENTOS_TEST_POSTGRES_URL and are
  destructive on that database; they must point at a dedicated scratch DB.
- Cross-module get_db override leakage is handled by each HTTP module asserting
  its own override in an autouse fixture (see treasury/webhook/rest_security).
- The ``pg`` marker tags tests that require a real PostgreSQL database.
"""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "pg: requires a real PostgreSQL database (AGENTOS_TEST_POSTGRES_URL)")
