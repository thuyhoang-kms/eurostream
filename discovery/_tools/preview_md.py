"""Preview assessment-report.md only (no workbook) when openpyxl is not installed.

  python3 preview_md.py <project dir> <out.md> <author-sections.md> [--include-unreviewed]
"""
import sys
import types
from pathlib import Path

stub = types.ModuleType("openpyxl")
stub.Workbook = object
styles = types.ModuleType("openpyxl.styles")
styles.Alignment = styles.Font = styles.PatternFill = lambda *a, **k: None
utils = types.ModuleType("openpyxl.utils")
utils.get_column_letter = lambda i: str(i)
sys.modules.update({"openpyxl": stub, "openpyxl.styles": styles, "openpyxl.utils": utils})

sys.path.insert(0, str(Path(__file__).parent))
import build_deliverables as bd  # noqa: E402

root, out, author_path = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), Path(sys.argv[3])
inc = "--include-unreviewed" in sys.argv
regs = bd.load_registers(root, inc)
intake = bd.md_text(root / "intake.md")
axis_c = "\n".join(l for l in intake.splitlines() if l.strip().startswith(">"))
suff_bad = [l for l in bd.md_text(root / "sufficiency.md").splitlines() if "❌" in l or "⚠️" in l]
names = {r.get("id") or r.get("object_id"): r.get("name") for n in ("inventory", "rationalization")
         for r in bd.load_registers(root, True)[n] if r.get("name")}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(bd.build_md(regs, root, axis_c, suff_bad, bd.parse_author_sections(author_path), None, intake, names),
               encoding="utf-8")
print(f"wrote {out}")
