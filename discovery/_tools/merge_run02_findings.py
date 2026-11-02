"""Merge run-02 findings (with migration_disposition) into registers/, on the user's instruction (2026-10-06).

Keeps the run-01 review stamp and records that the run-02 fields were merged at the user's request.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "eurostream"
reg_path = ROOT / "registers" / "findings.jsonl"
run = {json.loads(l)["id"]: json.loads(l)
       for l in (ROOT / "runs" / "2026-10-06_run-02" / "findings.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
now = datetime.now(timezone.utc).isoformat(timespec="seconds")
out = []
for line in reg_path.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    r = json.loads(line)
    new = run.get(r["id"])
    if new:
        merged = {**new, "status": r.get("status", "reviewed"), "reviewed_by": r.get("reviewed_by"),
                  "reviewed_at": r.get("reviewed_at"),
                  "merge_note": f"run-02 migration_disposition merged into registers on the user's instruction, {now}"}
        r = merged
    out.append(json.dumps(r, ensure_ascii=False))
reg_path.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"merged {sum(1 for l in out if 'merge_note' in l)} of {len(out)} findings")
