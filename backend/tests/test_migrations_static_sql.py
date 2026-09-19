"""Static PostgreSQL migration rendering checks.

The complete migration/backfill rehearsal still requires the destructive,
opt-in PostgreSQL suite. This lightweight test catches an earlier failure mode:
historical guarded migrations attempting database inspection while Alembic is
rendering offline SQL for a release review.
"""

from __future__ import annotations

import os
import subprocess
import sys
import sysconfig
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent


def test_postgresql_migrations_render_offline_sql() -> None:
    env = dict(os.environ)
    env["DATABASE_URL"] = "postgresql+psycopg://release_check:release_check@localhost:5432/action_control"
    code = (
        "import sys, sysconfig; "
        "sys.path.insert(0, sysconfig.get_paths()['purelib']); "
        "from alembic.config import main; "
        "main(['upgrade', 'head', '--sql'])"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "CREATE TABLE tenants" in result.stdout
    assert "CREATE TABLE audit_events" in result.stdout
    assert "event_sequence" in result.stdout
    assert "CREATE TABLE workforce_goals" in result.stdout
    assert "CREATE TABLE workforce_work_items" in result.stdout
