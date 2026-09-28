"""Fetch pinned documentation/features and current OSF word measures; retain hashes."""
from pathlib import Path
import hashlib
import json
import urllib.request
from urllib.parse import urlsplit, urlunsplit
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
REV = "46247ca2aea5876311acf6b59338880d0bf5449d"
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
records = []
manifest_path = ROOT / "data-manifest.json"
previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
previous_inputs = {r["path"]: r for r in previous["inputs"]} if previous else {}

def fetch(url, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        with urllib.request.urlopen(url, timeout=90) as response:
            final_url = response.url
            content = response.read(250_000_001)
            if len(content) > 250_000_000:
                raise ValueError("Input exceeds 250 MB download limit")
            target.write_bytes(content)
    else:
        old = previous_inputs.get(str(target.relative_to(ROOT)))
        if old and (old["source"] != url or old["sha256"] != hashlib.sha256(target.read_bytes()).hexdigest()):
            raise ValueError(f"Existing input differs from frozen manifest: {target}")
        final_url = old.get("resolved_url") if old else None
    # Redirects may contain expiring access signatures; retain only their location.
    if final_url:
        parts = urlsplit(final_url)
        final_url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    records.append(dict(path=str(target.relative_to(ROOT)), source=url,
                        resolved_url=final_url, bytes=target.stat().st_size,
                        sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    print(target.relative_to(ROOT), target.stat().st_size, flush=True)

base = f"https://raw.githubusercontent.com/DiLi-Lab/PoTeC/{REV}/"
for name in ["README.md", "CODEBOOK.md", "participants/README.md",
             "participants/participant_data.tsv", "additional_scripts/merge_reading_measures.py",
             "additional_scripts/compute_reading_measures.py"]:
    fetch(base + name, DATA / "source" / name)
for domain in "bp":
    for number in range(6):
        name = f"stimuli/word_features/word_features_{domain}{number}.tsv"
        fetch(base + name, DATA / "source" / name)
archive = DATA / "reading_measures_merged.zip"
fetch("https://osf.io/download/3ywhz", archive)
with zipfile.ZipFile(archive) as z:
    members = [n for n in z.namelist() if n.endswith(".tsv") and "__MACOSX" not in n]
    if len({Path(n).name for n in members}) != len(members):
        raise ValueError("Archive has colliding TSV basenames")
    for name in members:
        target = DATA / "reading_measures_merged" / Path(name).name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(z.read(name))
    print("Extracted TSV files:", len(members))
skill = ROOT.parents[1] / "skills/lme4-mixed-models"
skill_hashes = {str(p.relative_to(skill)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(skill.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}
manifest = dict(github_revision=REV, retrieved_at=datetime.now(timezone.utc).isoformat(),
                inputs=records, skill_files_sha256=skill_hashes,
                note="OSF archive is separately hashed; a Git revision does not pin its contents.")
if previous:
    if previous["inputs"] != records:
        raise ValueError("Inputs differ from frozen manifest")
    print("Existing input manifest verified; original receipt retained.")
else:
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
