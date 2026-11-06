"""Repro: does an erased customer come back after the next full Silver/Gold rebuild?

Synthetic data only (the project's own EventGenerator), a temp DuckDB file, no Turso, no bus.
Prints counts per layer after erasure and again after build_silver()/build_gold().
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

for k in list(os.environ):
    if "TURSO" in k:
        del os.environ[k]

from eurostream.governance.erasure import ErasureService  # noqa: E402
from eurostream.metrics import Metrics  # noqa: E402
from eurostream.config import Settings  # noqa: E402
from eurostream.producers import EventGenerator  # noqa: E402
from eurostream.warehouse import Warehouse  # noqa: E402
from eurostream.bus.sqlite import open_bus  # noqa: E402


def counts(wh: Warehouse, cid: str) -> dict[str, int]:
    q = {
        "bronze.orders": "SELECT count(*) FROM bronze.orders WHERE customer_id=?",
        "silver.customers": "SELECT count(*) FROM silver.customers WHERE customer_id=?",
        "silver.orders": "SELECT count(*) FROM silver.orders WHERE customer_id=?",
        "gold.customer_360": "SELECT count(*) FROM gold.customer_360 WHERE customer_id=?",
        "suppression_registry": "SELECT count(*) FROM governance.suppression_registry WHERE customer_id=?",
    }
    return {k: int(wh.conn.execute(v, (cid,)).fetchone()[0]) for k, v in q.items()}


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="es-repro-"))
    wh = Warehouse(tmp / "wh.duckdb", turso_url=None, turso_token=None)
    bus = open_bus(tmp / "events.db")
    gen = EventGenerator(Settings())
    orders = [gen.order() for _ in range(200)]
    for o in orders:
        wh.append_order(o)
    wh.build_silver()
    wh.build_gold()
    cid = orders[0].customer_id
    print("customer", "<synthetic id #0>")
    print("before_erasure", counts(wh, cid))
    svc = ErasureService(
        warehouse=wh,
        producer=bus,
        consumer=bus.consumer("erasure_requests", "repro", auto_offset_reset="earliest"),
        audit_log_path=tmp / "audit.jsonl",
        metrics=Metrics(tmp / "metrics.jsonl"),
        sla_seconds=60,
    )
    rid = svc.request_erasure(cid)
    ev = None
    from eurostream.models import ErasureRequested
    import time as _t
    ev = ErasureRequested(event_id=rid, request_id=rid, customer_id=cid, occurred_at=_t.time())
    svc.execute(ev)
    print("after_erasure", counts(wh, cid))
    wh.build_silver()
    wh.build_gold()
    print("after_full_rebuild", counts(wh, cid))
    row = wh.conn.execute(
        "SELECT email_hash IS NOT NULL FROM silver.customers WHERE customer_id=?", (cid,)
    ).fetchone()
    print("resurrected_silver_row_has_email_hash", None if row is None else bool(row[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
