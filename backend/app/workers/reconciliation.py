"""Run one bounded batch of durable, status-only reconciliation checks."""

from __future__ import annotations

import json

from app.db.session import SessionLocal
from app.services.reconciliation import ReconciliationService


def main() -> None:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL must be configured before starting the reconciliation worker")
    with SessionLocal() as db:
        report = ReconciliationService(db).run_due_checks()
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
