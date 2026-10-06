"""Copy reviewed findings into run-02 with migration_disposition set (status back to extracted for review)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "eurostream"
DISP = {
    "FND-01": "carried", "FND-02": "redesign", "FND-03": "carried", "FND-04": "redesign",
    "FND-05": "redesign", "FND-06": "carried", "FND-07": "redesign", "FND-08": "carried",
    "FND-09": "resolved-by-target", "FND-10": "resolved-by-target", "FND-11": "carried", "FND-12": "carried",
}
NOTE = {
    "FND-01": "Apply 50_grants_and_tags.sql and re-read information_schema before wave 1 exit.",
    "FND-02": "Production on an EU-region workspace (OQ-06); this one stays rehearsal.",
    "FND-04": "Bundle (databricks/dab) becomes the deployment source of truth.",
    "FND-05": "Bundle becomes source of truth; unpause after wave exit criteria.",
    "FND-07": "Retire Turso, or extend Databricks erasure to it (OQ-02).",
    "FND-09": "Databricks App: OBO SQL + signed preview token + Jobs runNow.",
    "FND-10": "Databricks reads the salt from spark conf eurostream.pii.salt (silver_pseudonymize.py:31).",
}
out = []
for line in (ROOT / "registers" / "findings.jsonl").read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    r = json.loads(line)
    r["migration_disposition"] = DISP[r["id"]]
    if r["id"] in NOTE:
        r["disposition_note"] = NOTE[r["id"]]
    if r["id"] == "FND-04":
        r["detail"] = ("Bundle defines 8 jobs (jobs.yml:15-368) incl. eurostream_fraud_continuous, quality_gate, "
                       "orchestrator. Workspace has 4 UI-created jobs: eurostream_bootstrap, eurostream_pipeline, "
                       "eurostream_export_lake, eurostream_art17_erasure.")
    r["status"] = "extracted"
    for k in ("reviewed_by", "reviewed_at"):
        r.pop(k, None)
    out.append(json.dumps(r, ensure_ascii=False))
dest = ROOT / "runs" / "2026-10-06_run-02" / "findings.jsonl"
dest.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"wrote {len(out)} findings to {dest}")
