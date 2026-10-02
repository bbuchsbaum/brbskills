#!/usr/bin/env python3
"""Scan a BIDS dataset's lightweight files and render a self-contained dashboard.

Standard library only. Image payloads are never read beyond the NIfTI header
(volume count and TR), and only when the file is locally present.

    python bids_atlas.py scan   ROOT [--derivatives DIR ...] -o model.json
    python bids_atlas.py render model.json [--findings findings.json] -o atlas.html
    python bids_atlas.py build  ROOT [...] -o atlas.html   # scan + render
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import functools
import gzip
import json
import math
import os
import re
import stat
import statistics
import struct
import zlib
import sys
from collections import Counter, defaultdict
from pathlib import Path

VERSION = "0.1.0"
SCHEMA = "bids-atlas/1"
HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "template.html"

SKIP_DIRS = {
    ".git",
    ".datalad",
    ".heudiconv",
    "node_modules",
    "__pycache__",
    ".ipynb_checkpoints",
}
IMAGE_EXT = (
    ".nii.gz",
    ".nii",
    ".gii",
    ".dtseries.nii",
    ".func.gii",
    ".h5",
    ".mgz",
    ".edf",
    ".bdf",
    ".set",
    ".fdt",
    ".vhdr",
    ".eeg",
    ".fif",
    ".snirf",
    ".tsv.gz",
    ".dscalar.nii",
    ".mat",
    ".x5",
)
TEXT_EXT = (
    ".json",
    ".tsv",
    ".bval",
    ".bvec",
    ".txt",
    ".md",
    ".html",
    ".svg",
    ".toml",
    ".yml",
    ".yaml",
    ".log",
    ".rst",
)
ENTITY_ORDER = [
    "sub",
    "ses",
    "task",
    "acq",
    "ce",
    "rec",
    "dir",
    "run",
    "mod",
    "echo",
    "flip",
    "inv",
    "mt",
    "part",
    "recording",
    "space",
    "res",
    "den",
    "label",
    "desc",
    "hemi",
    "from",
    "to",
    "mode",
    "fmapid",
    "model",
]
DATATYPES = {
    "func",
    "anat",
    "dwi",
    "fmap",
    "perf",
    "meg",
    "eeg",
    "ieeg",
    "beh",
    "pet",
    "micr",
    "nirs",
    "motion",
    "mrs",
}
TOP_LEVEL_OK = {
    "dataset_description.json",
    "README",
    "README.md",
    "README.txt",
    "README.rst",
    "CHANGES",
    "LICENSE",
    "participants.tsv",
    "participants.json",
    "samples.tsv",
    "samples.json",
    ".bidsignore",
    "CITATION.cff",
    "phenotype",
    "code",
    "derivatives",
    "sourcedata",
    "stimuli",
    "genetic_info.json",
    "scans.tsv",
    ".gitattributes",
    ".gitignore",
    ".git",
    ".datalad",
    "dataset_description.json",
}
JUNK = {".DS_Store", "Thumbs.db", "desktop.ini"}

# Common sidecar keys; used for "possible typo" detection only.
KNOWN_KEYS = set(
    """
RepetitionTime TaskName TaskDescription Instructions CogAtlasID CogPOID SliceTiming SliceEncodingDirection
PhaseEncodingDirection EffectiveEchoSpacing TotalReadoutTime EchoTime EchoTime1 EchoTime2 FlipAngle
MultibandAccelerationFactor ParallelReductionFactorInPlane ParallelAcquisitionTechnique PartialFourier
PartialFourierDirection Manufacturer ManufacturersModelName MagneticFieldStrength DeviceSerialNumber
StationName SoftwareVersions InstitutionName InstitutionAddress InstitutionalDepartmentName
ReceiveCoilName ReceiveCoilActiveElements CoilCombinationMethod PulseSequenceType ScanningSequence
SequenceVariant ScanOptions SequenceName PulseSequenceDetails NonlinearGradientCorrection MRAcquisitionType
MTState MTOffsetFrequency SpoilingState SpoilingType InversionTime DwellTime B0FieldIdentifier B0FieldSource
IntendedFor NumberOfVolumesDiscardedByScanner NumberOfVolumesDiscardedByUser DelayTime AcquisitionDuration
DelayAfterTrigger VolumeTiming Units TaskName EchoTrainLength PixelBandwidth ImagingFrequency
ImageType AcquisitionTime AcquisitionNumber SeriesNumber SeriesDescription ProtocolName BodyPartExamined
PatientPosition ProcedureStepDescription ConversionSoftware ConversionSoftwareVersion Modality
AcquisitionMatrixPE ReconMatrixPE BaseResolution ShimSetting TxRefAmp PhaseResolution InPlanePhaseEncodingDirectionDICOM
PercentPhaseFOV PercentSampling SAR RefLinesPE CoilString PhaseEncodingSteps FrequencyEncodingSteps
SpacingBetweenSlices SliceThickness BandwidthPerPixelPhaseEncode DerivedVendorReportedEchoSpacing
MatrixCoilMode PhaseEncodingPolarityGE BidsGuess WaterFatShift ImageOrientationPatientDICOM
ImageComments EstimatedEffectiveEchoSpacing EstimatedTotalReadoutTime SliceAcceleration
Name BIDSVersion DatasetType License Authors Acknowledgements HowToAcknowledge Funding EthicsApprovals
ReferencesAndLinks DatasetDOI GeneratedBy SourceDatasets HEDVersion DatasetLinks PipelineDescription
LongName Description Levels Sources RawSources SkullStripped Resolution Density Type SamplingFrequency
StartTime Columns TrialType onset duration trial_type response_time stim_file value HED
CogAtlasID TaskDescription Instructions SpatialReference Units
""".split()
)

# Overrides of these keys change analysis; others (AcquisitionTime, SAR, ...) vary per run by nature.
OVERRIDE_KEYS = {
    "RepetitionTime",
    "TaskName",
    "SliceTiming",
    "PhaseEncodingDirection",
    "EchoTime",
    "EffectiveEchoSpacing",
    "TotalReadoutTime",
    "MultibandAccelerationFactor",
    "IntendedFor",
    "B0FieldIdentifier",
    "B0FieldSource",
    "SliceEncodingDirection",
    "FlipAngle",
    "NumberOfVolumesDiscardedByScanner",
    "VolumeTiming",
    "DelayTime",
}

FD_STEP = 0.05

SNAKE_MOTION = ["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z"]
CAMEL_MOTION = ["X", "Y", "Z", "RotX", "RotY", "RotZ"]
FD_COLS = ["framewise_displacement", "FramewiseDisplacement"]
STD_DVARS_COLS = ["std_dvars", "stdDVARS"]
DVARS_COLS = ["dvars", "non-stdDVARS"]
GS_COLS = ["global_signal", "GlobalSignal"]

ENTITY_RE = re.compile(r"^([a-zA-Z]+)-([a-zA-Z0-9.+]+)$")


# ----------------------------------------------------------------------------- helpers


def plural(n: int, word: str) -> str:
    return f"{n:,} {word}{'' if n == 1 else 's'}"


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def split_ext(name: str) -> tuple[str, str]:
    for ext in (
        ".dtseries.nii",
        ".dscalar.nii",
        ".func.gii",
        ".surf.gii",
        ".shape.gii",
        ".label.gii",
        ".nii.gz",
        ".tsv.gz",
        ".tar.gz",
    ):
        if name.endswith(ext):
            return name[: -len(ext)], ext
    stem, dot, ext = name.rpartition(".")
    if not dot or not stem:
        return name, ""
    return stem, "." + ext


def parse_name(name: str) -> dict | None:
    """Return {'entities': {...}, 'suffix': str, 'ext': str} or None if not BIDS-like."""
    stem, ext = split_ext(name)
    parts = stem.split("_")
    if len(parts) < 2 or not parts[0].startswith("sub-"):
        # Inheritance-level sidecars like task-rest_bold.json have no sub entity.
        if len(parts) < 1:
            return None
    ents: dict[str, str] = {}
    suffix = parts[-1]
    for p in parts[:-1]:
        m = ENTITY_RE.match(p)
        if not m:
            return None
        ents[m.group(1)] = m.group(2)
    if ENTITY_RE.match(suffix) or not re.match(r"^[a-zA-Z0-9]+$", suffix):
        return None
    return {"entities": ents, "suffix": suffix, "ext": ext}


def norm_run(v):
    if v is None:
        return None
    try:
        return str(int(v))
    except ValueError:
        return v


def run_key(ents: dict, drop=("echo", "space", "res", "den", "desc", "recording")) -> str:
    """Canonical acquisition key: one per run, shared by raw files, events and derivatives.

    Echoes collapse into one run; part-mag is the default image, so only part-phase stays distinct.
    """
    bits = []
    for k in ENTITY_ORDER:
        if k in drop or k not in ents or (k == "part" and ents[k] == "mag"):
            continue
        v = norm_run(ents[k]) if k == "run" else ents[k]
        bits.append(f"{k}-{v}")
    return "_".join(bits)


def read_text(path: Path, limit: int | None = None) -> str | None:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(limit) if limit else fh.read()
    except OSError:
        return None


def read_json(path: Path):
    """Returns (obj, error)."""
    txt = read_text(path)
    if txt is None:
        return None, "unreadable"
    try:
        return json.loads(txt.lstrip("\ufeff")), None
    except json.JSONDecodeError as exc:
        return None, f"{exc.msg} (line {exc.lineno})"
    except RecursionError:
        return None, "nested too deeply to parse"


def read_tsv(path: Path, max_rows: int | None = None):
    """Returns (header, rows, error). Rows are lists of strings."""
    try:
        opener = gzip.open if str(path).endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8", errors="replace", newline="") as fh:
            reader = csv.reader(fh, delimiter="\t")
            header = next(reader, None)
            if header is None:
                return [], [], "empty file"
            header = [h.strip().lstrip("﻿") for h in header]
            rows = []
            for i, row in enumerate(reader):
                if max_rows is not None and i >= max_rows:
                    break
                if not row or (len(row) == 1 and not row[0].strip()):
                    continue
                rows.append(row)
            return header, rows, None
    except (OSError, UnicodeError, csv.Error) as exc:
        return None, None, str(exc)


def fnum(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x) if math.isfinite(x) else None
    s = str(x).strip()
    if s in ("", "n/a", "NA", "NaN", "nan", "N/A"):
        return None
    try:
        v = float(s)
        return v if math.isfinite(v) else None
    except ValueError:
        return None


def stats(vals):
    v = sorted(x for x in vals if x is not None)
    if not v:
        return None
    n = len(v)
    mean = sum(v) / n
    med = v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2
    return {"n": n, "min": v[0], "max": v[-1], "mean": mean, "median": med}


def rnd(x, d=4):
    if x is None:
        return None
    if isinstance(x, float):
        return round(x, d)
    return x


@functools.lru_cache(maxsize=None)
def typo_candidates(key: str) -> tuple[str, ...]:
    """Known BIDS keys within edit distance 1 (short keys) or 2 of an unknown key; cached per key."""
    lim = 1 if len(key) < 9 else 2
    return tuple(kk for kk in sorted(KNOWN_KEYS) if edit_distance(key.lower(), kk.lower(), 2) <= lim)


def edit_distance(a: str, b: str, cap: int = 3) -> int:
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def file_state(path: Path, st: os.stat_result | None) -> str:
    """present | annex | broken | placeholder"""
    try:
        if path.is_symlink():
            target = os.readlink(path)
            if not path.exists():
                return (
                    "annex"
                    if ".git/annex" in target or "annex/objects" in target
                    else "broken"
                )
            return "present" if path.stat().st_size > 0 else "placeholder"
        if st is None:
            st = path.stat()
        return "present" if st.st_size > 0 else "placeholder"
    except OSError:
        return "broken"


def nifti_header(path: Path):
    """Return {'nvols':int,'tr':float|None,'dims':[...]} or None. Reads at most 544 bytes."""
    try:
        opener = gzip.open if str(path).endswith(".gz") else open
        with opener(path, "rb") as fh:
            buf = fh.read(544)
    except (OSError, EOFError, gzip.BadGzipFile, zlib.error):
        return None
    if len(buf) < 348:
        return None
    for endian in ("<", ">"):
        size = struct.unpack(endian + "i", buf[:4])[0]
        if size == 348:
            dim = struct.unpack(endian + "8h", buf[40:56])
            pix = struct.unpack(endian + "8f", buf[76:108])
            units = buf[123]
            break
        if size == 540 and len(buf) >= 540:
            dim = struct.unpack(endian + "8q", buf[16:80])
            pix = struct.unpack(endian + "8d", buf[104:168])
            units = struct.unpack(endian + "i", buf[500:504])[0]
            break
    else:
        return None
    ndim = dim[0]
    if not 1 <= ndim <= 7:
        return None
    nvols = dim[4] if ndim >= 4 else 1
    tr = float(pix[4]) if ndim >= 4 else None
    tunit = units & 0x38
    if tr is not None:
        if tunit == 16:  # msec
            tr /= 1000.0
        elif tunit == 24:  # usec
            tr /= 1e6
    return {
        "nvols": int(nvols),
        "tr": rnd(tr, 5) if tr else None,
        "dims": [int(d) for d in dim[1 : ndim + 1]],
    }


# ----------------------------------------------------------------------------- walking


class Walk:
    """One pass over a tree, never following directory symlinks."""

    def __init__(self, root: Path, skip_top: set[str] = frozenset()):
        self.root = root
        self.files: list[tuple[str, os.stat_result]] = []  # relative posix path, lstat
        self.dirs: list[str] = []
        self.junk: list[str] = []
        self._walk(root, "", skip_top)

    def _walk(self, d: Path, rel: str, skip_top):
        try:
            entries = sorted(os.scandir(d), key=lambda e: e.name)
        except OSError:
            return
        for e in entries:
            r = f"{rel}/{e.name}" if rel else e.name
            if e.name in SKIP_DIRS or (not rel and e.name in skip_top):
                continue
            try:
                st = e.stat(follow_symlinks=False)
            except OSError:
                continue
            if stat.S_ISDIR(st.st_mode):
                self.dirs.append(r)
                self._walk(Path(e.path), r, skip_top)
            else:
                if e.name in JUNK or e.name.startswith("._"):
                    self.junk.append(r)
                self.files.append((r, st))


# ----------------------------------------------------------------------------- inheritance


class Sidecars:
    """BIDS inheritance resolution over every JSON sidecar in a dataset."""

    def __init__(self, root: Path, rel_jsons: list[str], findings: "Findings"):
        self.root = root
        self.by_dir: dict[str, list[tuple[str, dict, dict]]] = defaultdict(list)
        self.cache: dict[str, dict] = {}
        self.bad: dict[str, str] = {}
        self.empty: list[str] = []
        for rel in rel_jsons:
            name = rel.rsplit("/", 1)[-1]
            if name in ("dataset_description.json", "participants.json"):
                continue
            pn = parse_name(name)
            if not pn:
                continue
            if (root / rel).exists() and (root / rel).stat().st_size == 0:
                self.empty.append(rel)
                continue
            obj, err = read_json(root / rel)
            if err:
                self.bad[rel] = err
                continue
            if not isinstance(obj, dict):
                self.bad[rel] = "top level is not an object"
                continue
            d = rel.rsplit("/", 1)[0] if "/" in rel else ""
            self.by_dir[d].append((rel, pn, obj))

    def resolve(self, rel: str, pn: dict):
        """Merged metadata, per-key source, and overridden keys (value changed by a deeper file)."""
        parts = rel.split("/")[:-1]
        dirs = [""] + ["/".join(parts[: i + 1]) for i in range(len(parts))]
        merged, sources, overrides = {}, {}, []
        ents = pn["entities"]
        for d in dirs:
            cands = []
            for jrel, jpn, obj in self.by_dir.get(d, []):
                if jpn["suffix"] != pn["suffix"]:
                    continue
                je = jpn["entities"]
                if all(
                    ents.get(k) == v
                    or (k == "run" and norm_run(ents.get(k)) == norm_run(v))
                    for k, v in je.items()
                ):
                    cands.append((len(je), jrel, obj))
            for _, jrel, obj in sorted(cands):
                for k, v in obj.items():
                    if k in merged and merged[k] != v:
                        overrides.append({"key": k, "from": sources[k], "to": jrel})
                    merged[k] = v
                    sources[k] = jrel
        return merged, sources, overrides


class Inherited:
    """Nearest applicable non-JSON file (events.tsv, .bval, ...) under the inheritance principle."""

    def __init__(self, rels: list[str]):
        self.by_dir: dict[str, list[tuple[str, dict]]] = defaultdict(list)
        for rel in rels:
            pn = parse_name(rel.rsplit("/", 1)[-1])
            if pn:
                self.by_dir[rel.rsplit("/", 1)[0] if "/" in rel else ""].append(
                    (rel, pn)
                )

    def find(self, rel: str, ents: dict, suffix: str, ext: str):
        parts = rel.split("/")[:-1]
        dirs = [""] + ["/".join(parts[: i + 1]) for i in range(len(parts))]
        best = None
        for depth, d in enumerate(dirs):
            for frel, fpn in self.by_dir.get(d, []):
                if fpn["suffix"] != suffix or fpn["ext"] != ext:
                    continue
                fe = fpn["entities"]
                if all(
                    norm_run(ents.get(k)) == norm_run(v)
                    if k == "run"
                    else ents.get(k) == v
                    for k, v in fe.items()
                ):
                    score = (depth, len(fe))
                    if best is None or score > best[0]:
                        best = (score, frel)
        return best[1] if best else None


# ----------------------------------------------------------------------------- findings


class Findings:
    def __init__(self):
        self.items: dict[str, dict] = {}

    def add(
        self,
        fid: str,
        severity: str,
        category: str,
        title: str,
        detail: str = "",
        path: str | None = None,
        unit: str | None = None,
        total: int | None = None,
    ):
        """Group repeated findings by id; keep up to 50 example paths.

        `unit` counts distinct things (e.g. a run, not each of its echo files);
        `total` sets the count when only a sample of paths is passed.
        """
        f = self.items.get(fid)
        if f is None:
            f = {
                "id": fid,
                "severity": severity,
                "category": category,
                "title": title,
                "detail": detail,
                "paths": [],
                "count": 0,
                "source": "scanner",
            }
            self.items[fid] = f
            f["_units"] = set()
        key = unit if unit is not None else path
        if key is not None:
            if key in f["_units"]:
                return
            f["_units"].add(key)
        f["count"] = total if total is not None else f["count"] + 1
        if path and len(f["paths"]) < 50:
            f["paths"].append(path)

    def list(self):
        order = {"error": 0, "warn": 1, "info": 2}
        items = []
        for f in self.items.values():
            g = {k: v for k, v in f.items() if k != "_units"}
            if 50 < len(f["_units"]) <= 20000:
                g["units"] = sorted(f["_units"])
            items.append(g)
        return sorted(
            items,
            key=lambda f: (order.get(f["severity"], 3), f["category"], f["id"]),
        )


# ----------------------------------------------------------------------------- confounds


def classify_columns(cols: list[str]) -> dict:
    fam = Counter()
    for c in cols:
        lc = c.lower()
        if (
            re.match(r"^(trans|rot)_[xyz]", c)
            or c in CAMEL_MOTION
            or re.match(r"^(x|y|z|rot[xyz])(_|$)", lc)
        ):
            fam["motion"] += 1
        elif lc.startswith(("a_comp_cor", "acompcor", "c_comp_cor", "w_comp_cor")):
            fam["aCompCor"] += 1
        elif lc.startswith(("t_comp_cor", "tcompcor")):
            fam["tCompCor"] += 1
        elif lc.startswith("cosine"):
            fam["cosine"] += 1
        elif lc.startswith(("non_steady_state", "nonsteadystate")):
            fam["non-steady-state"] += 1
        elif lc.startswith("motion_outlier"):
            fam["motion outlier"] += 1
        elif lc.startswith(("global_signal", "globalsignal")):
            fam["global signal"] += 1
        elif lc.startswith(("csf", "white_matter", "whitematter", "csf_wm")):
            fam["tissue signal"] += 1
        elif lc in ("framewise_displacement", "framewisedisplacement", "rmsd"):
            fam["FD/RMSD"] += 1
        elif "dvars" in lc:
            fam["DVARS"] += 1
        elif lc.startswith(("aroma", "edge_comp", "crown")):
            fam["AROMA / other noise"] += 1
        else:
            fam["other"] += 1
    return dict(fam)


def decimate(vals: list, n: int, mode: str = "max") -> list:
    if len(vals) <= n:
        return vals
    out = []
    step = len(vals) / n
    for i in range(n):
        seg = [v for v in vals[int(i * step) : int((i + 1) * step)] if v is not None]
        if not seg:
            out.append(None)
        elif mode == "max":
            out.append(max(seg, key=abs))
        else:
            out.append(sum(seg) / len(seg))
    return out


def summarize_confounds(
    path: Path, sidecar: dict | None, fd_thresh=(0.2, 0.5), keep_motion=True
):
    header, rows, err = read_tsv(path)
    if err or header is None:
        return {"error": err or "unreadable"}
    ncols = len(header)
    ragged = sum(1 for r in rows if len(r) != ncols)
    idx = {c: i for i, c in enumerate(header)}

    def col(names):
        for nm in names:
            if nm in idx:
                i = idx[nm]
                return nm, [fnum(r[i]) if i < len(r) else None for r in rows]
        return None, None

    gen = (
        "snake"
        if any(c in idx for c in SNAKE_MOTION + ["framewise_displacement"])
        else (
            "camel"
            if any(c in idx for c in CAMEL_MOTION + ["FramewiseDisplacement"])
            else "unknown"
        )
    )
    out = {
        "n_vols": len(rows),
        "n_cols": ncols,
        "naming": gen,
        "families": classify_columns(header),
        "ragged_rows": ragged,
    }
    fdname, fd = col(FD_COLS)
    if fd:
        st = stats(fd)
        out["fd"] = {
            # Full precision: the page compares this against user thresholds; round only for display.
            "mean": st["mean"] if st else None,
            "median": rnd(st["median"]) if st else None,
            "max": rnd(st["max"]) if st else None,
        }
        for t in fd_thresh:
            out["fd"][f"n_gt_{t}"] = sum(1 for v in fd if v is not None and v > t)
        # Exact spike counts at 0.05 mm steps (0.05-2.00) so thresholds never depend on rounded traces.
        out["fd_spikes"] = [sum(1 for v in fd if v is not None and v > round(FD_STEP * (i + 1), 2)) for i in range(40)]
        out["trace_fd"] = [rnd(v, 3) for v in fd]
    _, sd = col(STD_DVARS_COLS)
    if sd:
        st = stats(sd)
        out["std_dvars"] = {
            "mean": st["mean"] if st else None,
            "max": rnd(st["max"]) if st else None,
            "n_gt_1.5": sum(1 for v in sd if v is not None and v > 1.5),
        }
        out["trace_std_dvars"] = [rnd(v, 3) for v in sd]
    _, gs = col(GS_COLS)
    if gs:
        out["trace_gs"] = [rnd(v, 2) for v in gs]
    if keep_motion:
        names = SNAKE_MOTION if gen == "snake" else CAMEL_MOTION
        mot = {}
        for nm in names:
            if nm in idx:
                i = idx[nm]
                mot[nm] = [rnd(fnum(r[i]) if i < len(r) else None, 4) for r in rows]
        if mot:
            out["trace_motion"] = mot
            # Peak absolute displacement per axis family (mm for trans, rad for rot).
            tr = [
                abs(v)
                for k, s in mot.items()
                if k.lower().startswith(("trans", "x", "y", "z"))
                and not k.lower().startswith("rot")
                for v in s
                if v is not None
            ]
            rt = [
                abs(v)
                for k, s in mot.items()
                if k.lower().startswith("rot")
                for v in s
                if v is not None
            ]
            out["max_abs_trans"] = rnd(max(tr), 3) if tr else None
            out["max_abs_rot_deg"] = rnd(math.degrees(max(rt)), 3) if rt else None
    nss = [
        c
        for c in header
        if c.lower().startswith(("non_steady_state", "nonsteadystate"))
    ]
    out["n_nonsteady"] = len(nss)
    mo = [c for c in header if c.lower().startswith("motion_outlier")]
    out["n_motion_outliers"] = len(mo)
    # CompCor variance explained from the sidecar
    if isinstance(sidecar, dict):
        comp = defaultdict(lambda: {"n": 0, "retained": 0, "cum_ve": None, "ve": []})
        for k, meta in sidecar.items():
            if not isinstance(meta, dict) or not isinstance(meta.get("Method"), str):
                continue
            if "compcor" not in meta["Method"].lower().replace("_", ""):
                continue
            method = meta["Method"]
            mask = str(meta.get("Mask", "")) or ""
            key = f"{method}:{mask}" if mask else method
            c = comp[key]
            c["n"] += 1
            if meta.get("Retained", True) in (True, "true", "True"):
                c["retained"] += 1
                ve = fnum(meta.get("VarianceExplained"))
                if ve is not None and k in idx:
                    c["ve"].append(ve)
                cv = fnum(meta.get("CumulativeVarianceExplained"))
                if cv is not None and k in idx:
                    c["cum_ve"] = max(cv, c["cum_ve"] or 0)
        if comp:
            out["compcor"] = {
                k: {
                    "n": v["n"],
                    "retained": v["retained"],
                    "lists_dropped": v["n"] > v["retained"],
                    "cum_ve": rnd(v["cum_ve"], 4),
                    "ve": [rnd(x, 4) for x in sorted(v["ve"], reverse=True)[:12]],
                }
                for k, v in sorted(comp.items())
            }
    return out


# ----------------------------------------------------------------------------- derivatives


def detect_pipeline(desc: dict | None, dirname: str) -> tuple[str, str | None]:
    name, version = None, None
    if isinstance(desc, dict):
        gb = desc.get("GeneratedBy")
        if isinstance(gb, list) and gb and isinstance(gb[0], dict):
            name, version = gb[0].get("Name"), gb[0].get("Version")
        pd = desc.get("PipelineDescription")
        if not name and isinstance(pd, dict):
            name, version = pd.get("Name"), pd.get("Version")
    name = name or dirname or "unknown"
    return str(name), (str(version) if version is not None else None)


def scan_derivative(
    root: Path, label: str, findings: Findings
):
    w = Walk(root)
    desc, derr = (
        read_json(root / "dataset_description.json")
        if (root / "dataset_description.json").exists()
        else (None, "missing")
    )
    name, version = detect_pipeline(desc, root.name)
    lname = name.lower()
    kind = (
        "fmriprep"
        if "fmriprep" in lname or "fmriprep" in root.name.lower()
        else ("mriqc" if "mriqc" in lname or "mriqc" in root.name.lower() else "other")
    )
    d = {
        "label": label,
        "name": name,
        "version": version,
        "kind": kind,
        "description": desc if isinstance(desc, dict) else None,
        "n_files": len(w.files),
        "subjects": [],
        "spaces": {},
        "res": {},
        "suffixes": {},
        "datatypes": {},
        "reports": [],
        "group_reports": [],
        "figures": {},
        "citation": None,
        "confounds": [],
        "logs": 0,
        "bytes": 0,
    }
    if derr:
        findings.add(
            f"deriv-desc-{label}",
            "warn",
            "derivatives",
            f"{label}: dataset_description.json {'missing' if derr == 'missing' else 'invalid'}",
            "Derivative datasets should declare DatasetType and GeneratedBy.",
            f"{label}/dataset_description.json",
        )
    elif isinstance(desc, dict):
        if desc.get("DatasetType") != "derivative":
            findings.add(
                f"deriv-type-{label}",
                "info",
                "derivatives",
                f"{label}: DatasetType is not 'derivative'",
                f"Found {desc.get('DatasetType')!r}.",
                f"{label}/dataset_description.json",
            )
        if not desc.get("GeneratedBy") and not desc.get("PipelineDescription"):
            findings.add(
                f"deriv-gen-{label}",
                "warn",
                "derivatives",
                f"{label}: no GeneratedBy",
                "Pipeline provenance is unrecorded.",
                f"{label}/dataset_description.json",
            )
    subs, spaces, res, suff, dts = set(), Counter(), Counter(), Counter(), Counter()
    conf_files = []
    for rel, st in w.files:
        d["bytes"] += st.st_size
        if "/" not in rel and re.match(r"^sub-[A-Za-z0-9]+(_[A-Za-z0-9.+_-]*)?\.html$", rel) and st.st_size == 0:
            d["reports_empty"] = d.get("reports_empty", 0) + 1
        name_ = rel.rsplit("/", 1)[-1]
        if "/" not in rel and re.match(r"^group_[A-Za-z0-9]+\.html$", name_):
            d["group_reports"].append(rel)
        if "/" not in rel and re.match(r"^sub-[A-Za-z0-9]+(_[A-Za-z0-9.+_-]*)?\.html$", name_):
            d["reports"].append(rel)
        if "/figures/" in f"/{rel}" and name_.endswith((".svg", ".png", ".html")):
            m = re.match(r"^(sub-[A-Za-z0-9]+)", name_)
            if m:
                d["figures"][m.group(1)] = d["figures"].get(m.group(1), 0) + 1
        if rel.startswith("logs/") or "/log/" in rel:
            d["logs"] += 1
            if (
                name_.upper().startswith("CITATION")
                and name_.endswith((".md", ".txt"))
                and d["citation"] is None
            ):
                d["citation"] = read_text(root / rel, 6000)
        pn = parse_name(name_)
        if not pn:
            continue
        e = pn["entities"]
        if "sub" in e:
            subs.add(e["sub"])
        if "space" in e:
            spaces[e["space"]] += 1
        if "res" in e:
            res[e["res"]] += 1
        suff[pn["suffix"]] += 1
        parts = rel.split("/")
        if len(parts) >= 2 and parts[-2] in DATATYPES:
            dts[parts[-2]] += 1
        if (
            name_.endswith("_desc-confounds_timeseries.tsv")
            or name_.endswith("_desc-confounds_regressors.tsv")
            or name_.endswith("_bold_confounds.tsv")
        ):
            conf_files.append((rel, pn))
    d["subjects"] = sorted(subs)
    d["spaces"], d["res"], d["suffixes"], d["datatypes"] = (
        dict(spaces),
        dict(res),
        dict(suff.most_common(40)),
        dict(dts),
    )
    d["reports"] = sorted(d["reports"])
    if kind == "mriqc":
        d["iqms"], d["iqms_anat"] = read_mriqc(root, w)
        d["fd_thres"], d["fd_thres_source"] = mriqc_fd_thres(root, w)
        mriqc_outliers(d, label, findings)
    keep_motion = len(conf_files) <= 600
    for rel, pn in sorted(conf_files):
        sj = None
        jp = (root / rel).with_name(rel.rsplit("/", 1)[-1][:-4] + ".json")
        if jp.exists() and jp.stat().st_size == 0:
            findings.add(
                "json-empty",
                "warn",
                "metadata",
                "Zero-byte JSON files",
                "Empty sidecars carry no metadata (often an interrupted copy or an un-fetched placeholder).",
                f"{label}/{jp.relative_to(root).as_posix()}",
            )
        elif jp.exists():
            sj, jerr = read_json(jp)
            if jerr:
                findings.add(
                    "json-invalid",
                    "error",
                    "metadata",
                    "Invalid JSON files",
                    "These files do not parse.",
                    f"{label}/{jp.relative_to(root).as_posix()}",
                )
        state = file_state(root / rel, None)
        e = pn["entities"]
        rec = {
            "path": f"{label}/{rel}",
            "key": run_key(e),
            "sub": e.get("sub"),
            "ses": e.get("ses"),
            "task": e.get("task"),
            "run": norm_run(e.get("run")),
            "acq": e.get("acq"),
            "dir": e.get("dir"),
            "state": state,
        }
        if state == "present":
            rec.update(summarize_confounds(root / rel, sj, keep_motion=keep_motion))
        d["confounds"].append(rec)
    return d


MRIQC_BOLD = ("tsnr", "fd_mean", "fd_perc", "fd_num", "dvars_std", "aqi", "aor", "gcor", "snr", "fwhm_avg", "efc",
              "fber", "dummy_trs", "size_t", "spacing_tr", "gsr_x", "gsr_y")
MRIQC_ANAT = ("cjv", "cnr", "snr_total", "efc", "fber", "fwhm_avg", "wm2max", "qi_1", "qi_2", "inu_med")


def read_mriqc(root: Path, w: "Walk"):
    """Per-run IQMs from group_bold.tsv (preferred) or per-run JSONs."""

    def rows_from_group(name, keep):
        p = root / name
        if not p.exists() or p.stat().st_size == 0:
            return None
        header, rows, err = read_tsv(p)
        if err or not header or "bids_name" not in header:
            return None
        out = []
        for r in rows:
            rec = dict(zip(header, r))
            out.append((rec["bids_name"], {k: fnum(rec.get(k)) for k in keep if k in rec}))
        return out

    def rows_from_json(suffix, keep):
        out = []
        for rel, st in w.files:
            if rel.endswith(f"_{suffix}.json") and "/" in rel and st.st_size > 0:
                obj, err = read_json(root / rel)
                if isinstance(obj, dict):
                    out.append((rel.rsplit("/", 1)[-1][:-5], {k: fnum(obj.get(k)) for k in keep if k in obj}))
        return out

    bold = rows_from_group("group_bold.tsv", MRIQC_BOLD)
    if bold is None:
        bold = rows_from_json("bold", MRIQC_BOLD)
    anat = rows_from_group("group_T1w.tsv", MRIQC_ANAT)
    if anat is None:
        anat = rows_from_json("T1w", MRIQC_ANAT)
    res_b, res_a = [], []
    for name, metrics in bold:
        pn = parse_name(name + ".nii.gz")
        if not pn:
            continue
        e = pn["entities"]
        res_b.append({"key": run_key(e), "sub": e.get("sub"), "ses": e.get("ses"), "task": e.get("task"),
                      "run": norm_run(e.get("run")), "echo": e.get("echo"), "m": metrics})
    for name, metrics in anat:
        pn = parse_name(name + ".nii.gz")
        if pn:
            res_a.append({"sub": pn["entities"].get("sub"), "ses": pn["entities"].get("ses"), "name": name, "m": metrics})
    return res_b, res_a


def mriqc_fd_thres(root: Path, w: "Walk"):
    """fd_thres from the first non-empty per-run IQM JSON's provenance, if recorded."""
    for rel, st in w.files:
        if rel.endswith("_bold.json") and "/" in rel and st.st_size > 0:
            obj, err = read_json(root / rel)
            if isinstance(obj, dict):
                v = ((obj.get("provenance") or {}).get("settings") or {}).get("fd_thres")
                if fnum(v) is not None:
                    return fnum(v), rel
    return None, None


def scan_lengths(bold: list, derivs: list, findings: "Findings"):
    """Volumes per raw run from the header, else confounds rows, else MRIQC size_t; then check events."""
    conf, iqm = {}, {}
    for d in derivs:
        for c in d.get("confounds", []):
            if c.get("n_vols"):
                conf.setdefault(c["key"], c["n_vols"])
        for q in d.get("iqms", []):
            m = q.get("m") or {}
            # MRIQC's size_t excludes the dummy volumes it detected; the acquired series is size_t + dummy_trs.
            if m.get("size_t"):
                iqm.setdefault(q["key"], int(m["size_t"]) + int(m.get("dummy_trs") or 0))
    checked, with_events = set(), set()
    for r in bold:
        ek = r["key"]
        nv, src = None, None
        if r.get("hdr", {}).get("nvols"):
            nv, src = r["hdr"]["nvols"], "NIfTI header"
        elif ek in conf:
            nv, src = conf[ek], "fMRIPrep confounds rows"
        elif ek in iqm:
            nv, src = iqm[ek], "MRIQC size_t + dummy_trs"
        tr = fnum(r.get("meta", {}).get("RepetitionTime"))
        if nv:
            r["nvols"], r["nvols_source"] = nv, src
            if tr:
                r["scan_seconds"] = rnd(nv * tr, 2)
        ev = r.get("events") or {}
        if not ev.get("n"):
            continue
        with_events.add(ek)
        if not r.get("scan_seconds") or ek in checked:
            continue
        checked.add(ek)
        if ev.get("end", 0) > r["scan_seconds"] + tr:
            findings.add(
                "events-past-end",
                "warn",
                "events",
                "Events extend past the end of the scan",
                "Flagged when the last event ends more than one TR after volumes × TR.",
                f"{r.get('events_path')}: last event ends {ev['end']:.1f} s, scan {r['scan_seconds']:.1f} s ({src})",
                unit=ek,
            )
    if with_events and len(checked) < len(with_events):
        findings.add(
            "events-unchecked",
            "info",
            "events",
            f"Scan length unknown for {len(with_events) - len(checked)} of {len(with_events)} runs with events",
            "No local image header, confounds or MRIQC volume count, so events-past-end was not checked for these.",
        )


def sources_of(r: dict, key: str) -> str:
    src = (r.get("meta_src") or {}).get(key)
    return f"{r['path']} (from {src})" if src and src != r["path"].rsplit(".nii", 1)[0] + ".json" else r["path"]


# (metric, direction, label): direction +1 flags high values, -1 flags low ones.
# Floors keep a tight distribution from flagging values that are fine in absolute terms.
MRIQC_OUTLIER_METRICS = (("tsnr", -1, "low tSNR", None), ("fd_mean", 1, "high mean FD", 0.25),
                         ("dvars_std", 1, "high std DVARS", 1.5), ("aqi", 1, "high AFNI quality index", None))


def mriqc_outliers(d: dict, label: str, findings: "Findings", z: float = 3.5):
    """Robust (median/MAD) outliers per task and echo; a screening aid, not a verdict."""
    groups = defaultdict(list)
    for q in d.get("iqms", []):
        groups[(q.get("task"), q.get("echo"))].append(q)
    echoes = sorted({q.get("echo") for q in d.get("iqms", []) if q.get("echo")}, key=lambda e: int(e) if str(e).isdigit() else 0)
    report_echo = echoes[(len(echoes) - 1) // 2] if echoes else None
    d["report_echo"] = report_echo
    for (task, echo), qs in groups.items():
        if len(qs) < 8:
            continue
        # Per-echo flags drive the plots; findings use one echo so counts match the page's default view.
        first_echo = echoes[0] if echoes else None
        for metric, sign, what, floor in MRIQC_OUTLIER_METRICS:
            vals = [q["m"].get(metric) for q in qs if q["m"].get(metric) is not None]
            if len(vals) < 8:
                continue
            med = statistics.median(vals)
            mad = statistics.median(abs(v - med) for v in vals) * 1.4826
            if not mad:
                continue
            for q in qs:
                v = q["m"].get(metric)
                if v is None or sign * (v - med) / mad <= z or (floor is not None and v <= floor):
                    continue
                q.setdefault("outliers", []).append(metric)
                if echo != (first_echo if metric in ("fd_mean",) else report_echo):
                    continue
                findings.add(
                    f"mriqc-outlier-{metric}-{label}",
                    "warn",
                    "quality",
                    f"{label}: runs with {what} (MRIQC)",
                    f"More than {z} robust SDs from the median of runs with the same task"
                    + (" and echo" if echo else "")
                    + (f", and beyond an absolute floor of {floor:g}" if floor is not None else "")
                    + ". A screening flag; open the MRIQC report before excluding.",
                    f"{q['key']}{'_echo-' + echo if echo else ''}: {metric} {v:g} (median {med:g})",
                    unit=q["key"],
                )


def finalize_traces(confounds: list, max_points_total: int = 1_500_000):
    """Keep the embedded page small: decimate traces when the dataset is large."""
    total = sum(len(c.get("trace_fd") or []) for c in confounds) or 1
    per_run = None
    if total > max_points_total:
        per_run = max(120, int(max_points_total / max(1, len(confounds))))
    for c in confounds:
        if per_run:
            c["decimated"] = per_run
            for k in ("trace_fd", "trace_std_dvars"):
                if c.get(k):
                    c[k] = decimate(c[k], per_run, "max")
            if c.get("trace_gs"):
                c["trace_gs"] = decimate(c["trace_gs"], per_run, "mean")
            if c.get("trace_motion"):
                c["trace_motion"] = {
                    k: decimate(v, per_run, "mean")
                    for k, v in c["trace_motion"].items()
                }


# ----------------------------------------------------------------------------- raw scan


def detect_openneuro(root: Path, desc: dict | None) -> tuple[bool, str]:
    """Strong evidence only: an OpenNeuro DatasetDOI, or a git/DataLad remote hosted by OpenNeuro.

    A mention in ReferencesAndLinks (e.g. a task borrowed from an OpenNeuro dataset) or a
    folder name like ds000001 is not proof that these data are the public release.
    """
    doi = str((desc or {}).get("DatasetDOI", "")) if isinstance(desc, dict) else ""
    if re.search(r"10\.18112/openneuro\.ds\d{6}", doi, re.I):
        return True, "OpenNeuro DatasetDOI in dataset_description.json"
    for cfg in (root / ".git" / "config", root / ".datalad" / "config"):
        t = read_text(cfg, 20000) if cfg.is_file() else None
        for line in (t or "").splitlines():
            m = re.match(r"\s*url\s*=\s*(\S+)", line)
            if m and re.search(r"(^|[/@.])openneuro\.org[/:]|github\.com[/:]OpenNeuroDatasets/", m.group(1), re.I):
                return True, f"OpenNeuro remote in {cfg.relative_to(root).as_posix()}"
    if re.search(r"ds\d{6}", root.name):
        return False, "folder name looks like an OpenNeuro accession, but no OpenNeuro DOI or remote confirms it"
    return False, "not recognized as an OpenNeuro dataset"

def summarize_events(path: Path):
    header, rows, err = read_tsv(path)
    if err or header is None:
        return {"error": err or "unreadable"}
    idx = {c: i for i, c in enumerate(header)}
    out = {"n": len(rows), "columns": header, "issues": []}
    if "onset" not in idx or "duration" not in idx:
        out["issues"].append("missing onset/duration column")
    tt_col = "trial_type" if "trial_type" in idx else None
    out["type_column"] = tt_col
    if tt_col is None:
        # Fall back to the most condition-like categorical column, marked as inferred.
        best = None
        for c, i in idx.items():
            if c in ("onset", "duration", "sample", "response_time", "HED"):
                continue
            vals = [r[i] for r in rows if i < len(r) and r[i] not in ("", "n/a")]
            levels = set(vals)
            named = bool(re.search(r"cond|type|trial|stim|event|categ|block", c, re.I))
            # Conditions repeat; an all-unique column is an ID unless its name says otherwise.
            if not vals or not 2 <= len(levels) <= 24 or (len(levels) == len(vals) and not named):
                continue
            if not named and len(levels) > 0.5 * len(vals):
                continue
            numeric = sum(fnum(v) is not None for v in vals) / len(vals)
            score = (
                named,
                numeric < 0.5,
                -len(levels),
            )
            if best is None or score > best[0]:
                best = (score, c)
        if best:
            tt_col = best[1]
            out["type_column_inferred"] = tt_col
    ev, counts, durs = [], Counter(), defaultdict(list)
    neg, na_onset, end = 0, 0, 0.0
    prev = None
    nonmono = 0
    for r in rows:
        on = fnum(r[idx["onset"]]) if "onset" in idx and idx["onset"] < len(r) else None
        du = (
            fnum(r[idx["duration"]])
            if "duration" in idx and idx["duration"] < len(r)
            else None
        )
        tt = r[idx[tt_col]] if tt_col and idx[tt_col] < len(r) else "(none)"
        if on is None:
            na_onset += 1
            continue
        if on < 0:
            neg += 1
        if prev is not None and on < prev:
            nonmono += 1
        prev = on
        counts[tt] += 1
        if du is not None:
            durs[tt].append(du)
        end = max(end, on + (du or 0))
        if len(ev) < 3000:
            ev.append([rnd(on, 3), rnd(du, 3) if du is not None else None, tt])
    out.update(
        {
            "trial_types": dict(counts.most_common()),
            "end": rnd(end, 3),
            "n_negative": neg,
            "n_na_onset": na_onset,
            "n_unsorted": nonmono,
            "events": ev,
            "durations": {k: rnd(stats(v)["median"], 3) for k, v in durs.items() if v},
        }
    )
    return out


def scan(
    root: Path, extra_derivs: list[Path] | None = None, participants_mode: str = "auto"
) -> dict:
    root = root.resolve()
    findings = Findings()
    w = Walk(root, skip_top={"derivatives", "sourcedata"})
    model: dict = {
        "schema": SCHEMA,
        "tool": f"bids-atlas {VERSION}",
        "generated": now_iso(),
        "root_name": root.name,
    }

    # dataset_description
    dd_path = root / "dataset_description.json"
    desc, derr = read_json(dd_path) if dd_path.exists() else (None, "missing")
    if derr == "missing":
        findings.add(
            "dd-missing",
            "error",
            "dataset",
            "dataset_description.json is missing",
            "Every BIDS dataset needs one at the root.",
            "dataset_description.json",
        )
    elif derr:
        findings.add(
            "dd-invalid",
            "error",
            "dataset",
            "dataset_description.json does not parse",
            derr,
            "dataset_description.json",
        )
    elif isinstance(desc, dict):
        for k in ("Name", "BIDSVersion"):
            if not desc.get(k):
                findings.add(
                    f"dd-{k}",
                    "error",
                    "dataset",
                    f"dataset_description.json lacks {k}",
                    "",
                    "dataset_description.json",
                )
        for k in ("License", "Authors"):
            if not desc.get(k):
                findings.add(
                    f"dd-{k}",
                    "info",
                    "dataset",
                    f"dataset_description.json lacks {k}",
                    "Recommended field.",
                    "dataset_description.json",
                )
    model["description"] = desc if isinstance(desc, dict) else None
    is_deriv_root = isinstance(desc, dict) and desc.get("DatasetType") == "derivative"
    model["root_is_derivative"] = is_deriv_root
    is_openneuro, on_evidence = detect_openneuro(root, model["description"])
    model["openneuro"] = is_openneuro
    model["openneuro_evidence"] = on_evidence

    readme = next(
        (
            root / n
            for n in ("README", "README.md", "README.txt", "README.rst")
            if (root / n).exists()
        ),
        None,
    )
    model["readme"] = read_text(readme, 12000) if readme else None
    if not readme:
        findings.add(
            "readme-missing",
            "warn",
            "dataset",
            "No README",
            "A README is required by BIDS.",
        )
    changes = root / "CHANGES"
    model["changes"] = read_text(changes, 4000) if changes.exists() else None
    bidsignore = (
        read_text(root / ".bidsignore") if (root / ".bidsignore").exists() else None
    )
    model["bidsignore"] = bidsignore
    ignore_pats = []
    for line in (bidsignore or "").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            rx = (
                re.escape(line.strip("/"))
                .replace(r"\*\*", ".*")
                .replace(r"\*", "[^/]*")
                .replace(r"\?", ".")
            )
            ignore_pats.append(re.compile(rf"(^|/){rx}($|/)"))

    def ignored(rel):
        return any(p.search(rel) for p in ignore_pats)

    # Inventory
    rel_jsons = [r for r, _ in w.files if r.endswith(".json")]
    side = Sidecars(root, rel_jsons, findings)
    for rel in side.empty:
        findings.add(
            "json-empty",
            "warn",
            "metadata",
            "Zero-byte JSON files",
            "Empty sidecars carry no metadata (often an interrupted copy or an un-fetched placeholder).",
            rel,
        )
    for rel, err in side.bad.items():
        findings.add(
            "json-invalid",
            "error",
            "metadata",
            "Invalid JSON files",
            "These files do not parse.",
            rel,
        )

    inh = Inherited(
        [
            r
            for r, _ in w.files
            if r.endswith(("_events.tsv", ".bval", ".bvec"))
            or r in ("dwi.bval", "dwi.bvec")
        ]
    )
    states = Counter()
    annex_paths: list[str] = []
    bytes_present = 0
    ext_counts = Counter()
    dt_counts = defaultdict(Counter)
    subjects, sessions = set(), set()
    sub_sessions = defaultdict(set)
    bold, anat, dwi, fmap, other_runs = [], [], [], [], []
    events_files, physio = {}, set()
    scans_tsv = []
    nonbids = []
    file_index = set()
    tree_counts = Counter()
    for rel, st in w.files:
        file_index.add(rel)
        name = rel.rsplit("/", 1)[-1]
        parts = rel.split("/")
        _, ext = split_ext(name)
        ext_counts[ext or "(none)"] += 1
        top = parts[0]
        tree_counts[top] += 1
        if len(parts) == 1:
            if (
                name not in TOP_LEVEL_OK
                and not name.startswith(".")
                and not ignored(rel)
                and not parse_name(name)
            ):
                nonbids.append(rel)
            continue
        if top in ("code", "stimuli", "phenotype", "sourcedata"):
            continue
        pn = parse_name(name)
        if pn is None:
            if not ignored(rel) and name not in JUNK and not name.startswith("."):
                nonbids.append(rel)
            continue
        e = pn["entities"]
        if pn["suffix"] == "scans" and ext == ".tsv":
            scans_tsv.append(rel)
            continue
        if "sub" not in e or not top.startswith("sub-"):
            if top.startswith("sub-") and not ignored(rel) and not name.startswith("."):
                nonbids.append(rel)
            continue
        if is_deriv_root and ("space" in e or "desc" in e or "res" in e or "den" in e):
            continue
        if f"sub-{e['sub']}" != top:
            findings.add(
                "sub-mismatch",
                "error",
                "naming",
                "File sub- entity disagrees with its folder",
                "",
                rel,
            )
        subjects.add(e["sub"])
        if "ses" in e:
            sessions.add(e["ses"])
            sub_sessions[e["sub"]].add(e["ses"])
        dtype = parts[-2] if parts[-2] in DATATYPES else None
        if dtype is None:
            # Subject- and session-level files (inherited sidecars, scans/sessions tables) are BIDS.
            subject_level = len(parts) == 2 or (len(parts) == 3 and parts[1].startswith("ses-"))
            if not subject_level and not ignored(rel):
                nonbids.append(rel)
            continue
        dt_counts[dtype][pn["suffix"]] += 1
        is_image = ext in IMAGE_EXT and ext != ".tsv.gz"
        if ext == ".tsv.gz" and pn["suffix"] in ("physio", "stim"):
            physio.add(run_key(e, drop=("recording",)))
        if pn["suffix"] == "events" and ext == ".tsv":
            events_files[run_key(e)] = rel
        if not is_image:
            continue
        s = file_state(root / rel, st)
        states[s] += 1
        if s == "annex":
            annex_paths.append(rel)
        if s == "present":
            bytes_present += (root / rel).stat().st_size
        meta, sources, overrides = side.resolve(rel, pn)
        for ov in overrides:
            if ov["key"] not in OVERRIDE_KEYS:
                continue
            findings.add(
                f"inherit-override-{ov['key']}",
                "info",
                "metadata",
                f"{ov['key']} set at a higher level is overridden for some files",
                "Legal under the inheritance principle, but worth knowing: a value set at a higher level is "
                "replaced for this file.",
                f"{rel} :: {ov['key']}",
            )
        rec = {
            "path": rel,
            "sub": e.get("sub"),
            "ses": e.get("ses"),
            "task": e.get("task"),
            "acq": e.get("acq"),
            "dir": e.get("dir"),
            "run": norm_run(e.get("run")),
            "echo": e.get("echo"),
            "suffix": pn["suffix"],
            "datatype": dtype,
            "state": s,
            "key": run_key(e),
            "ext": ext,
        }
        if s == "present" and ext in (".nii", ".nii.gz"):
            hdr = nifti_header(root / rel)
            if hdr:
                rec["hdr"] = hdr
        if (
            dtype == "func"
            and pn["suffix"] in ("bold", "cbv", "sbref")
            or dtype == "func"
        ):
            keep = (
                "RepetitionTime",
                "TaskName",
                "SliceTiming",
                "PhaseEncodingDirection",
                "EchoTime",
                "MultibandAccelerationFactor",
                "EffectiveEchoSpacing",
                "TotalReadoutTime",
                "FlipAngle",
                "Manufacturer",
                "ManufacturersModelName",
                "MagneticFieldStrength",
                "B0FieldSource",
                "NumberOfVolumesDiscardedByScanner",
                "DelayTime",
                "VolumeTiming",
                "SliceEncodingDirection",
                "ParallelReductionFactorInPlane",
            )
            m = {k: meta[k] for k in keep if k in meta}
            st_ = m.pop("SliceTiming", None)
            if isinstance(st_, list) and not st_:
                findings.add(
                    "st-empty",
                    "warn",
                    "metadata",
                    "SliceTiming is an empty list",
                    "Present but empty; slice-timing correction will be skipped or fail.",
                    sources.get("SliceTiming", rel),
                )
            if isinstance(st_, list) and not st_:
                m["SliceTiming"] = {"n": 0, "order": "empty list", "min": None, "max": None}
            if isinstance(st_, list) and st_:
                vals = [fnum(x) for x in st_]
                vals = [v for v in vals if v is not None]
                if vals:
                    m["SliceTiming"] = {
                        "n": len(st_),
                        "min": rnd(min(vals), 4),
                        "max": rnd(max(vals), 4),
                        "order": slice_order(vals),
                    }
            rec["meta"] = m
            rec["meta_src"] = {k: sources[k] for k in m if k in sources}
            rec["keys"] = sorted(meta.keys())
            if pn["suffix"] in ("bold", "cbv"):
                bold.append(rec)
            elif pn["suffix"] == "sbref":
                other_runs.append(rec)
            else:
                other_runs.append(rec)
        elif dtype == "anat":
            rec["meta"] = {
                k: meta[k]
                for k in (
                    "EchoTime",
                    "RepetitionTime",
                    "InversionTime",
                    "FlipAngle",
                    "MRAcquisitionType",
                    "Manufacturer",
                    "ManufacturersModelName",
                    "MagneticFieldStrength",
                )
                if k in meta
            }
            rec["keys"] = sorted(meta.keys())
            anat.append(rec)
        elif dtype == "dwi":
            rec["meta"] = {
                k: meta[k]
                for k in (
                    "PhaseEncodingDirection",
                    "TotalReadoutTime",
                    "EchoTime",
                    "RepetitionTime",
                    "MultibandAccelerationFactor",
                )
                if k in meta
            }
            bvrel = inh.find(rel, e, "dwi", ".bval")
            bv = root / bvrel if bvrel else None
            if bv is not None and bv.exists():
                txt = read_text(bv) or ""
                b = [fnum(x) for x in txt.split()]
                b = [x for x in b if x is not None]
                shells = Counter(int(round(x / 50.0) * 50) for x in b)
                rec["bvals"] = {"n": len(b), "shells": dict(sorted(shells.items()))}
            else:
                findings.add(
                    "dwi-nobval", "warn", "dwi", "DWI image without .bval", "", rel
                )
            rec["keys"] = sorted(meta.keys())
            dwi.append(rec)
        elif dtype == "fmap":
            itf = meta.get("IntendedFor")
            if isinstance(itf, str):
                itf = [itf]
            rec["meta"] = {
                k: meta[k]
                for k in (
                    "EchoTime1",
                    "EchoTime2",
                    "EchoTime",
                    "PhaseEncodingDirection",
                    "TotalReadoutTime",
                    "B0FieldIdentifier",
                    "Units",
                )
                if k in meta
            }
            rec["intended_for"] = itf if isinstance(itf, list) else []
            rec["b0id"] = meta.get("B0FieldIdentifier")
            rec["keys"] = sorted(meta.keys())
            fmap.append(rec)
        else:
            rec["keys"] = sorted(meta.keys())
            other_runs.append(rec)

        # key typos (once per file, raw only)
        for k in meta:
            if k in KNOWN_KEYS:
                continue
            near = typo_candidates(k)
            if near:
                findings.add(
                    f"typo-{k}",
                    "warn",
                    "metadata",
                    f"Sidecar key '{k}' looks like a typo of '{near[0]}'",
                    "Unknown keys are ignored by BIDS tools; the intended value is effectively missing.",
                    sources.get(k, rel),
                )

    model["subjects"] = sorted(subjects)
    model["sessions"] = sorted(sessions)
    model["sub_sessions"] = {s: sorted(v) for s, v in sub_sessions.items()}
    model["datatypes"] = {k: dict(v) for k, v in sorted(dt_counts.items())}
    model["extensions"] = dict(ext_counts.most_common(30))
    model["image_states"] = dict(states)
    model["bytes_present"] = bytes_present
    model["n_files"] = len(w.files)
    model["tree"] = dict(tree_counts.most_common())
    model["junk"] = w.junk[:50]
    model["nonbids"] = nonbids[:200]
    model["n_nonbids"] = len(nonbids)

    # Image state findings
    nimg = sum(states.values())
    if states.get("annex"):
        findings.add(
            "annex",
            "info",
            "files",
            f"{states['annex']} of {nimg} image files are un-fetched git-annex links",
            "Expected for a text-only clone. Header-derived checks (volume counts) are unavailable for these.",
            annex_paths[0] if annex_paths else None,
            total=states["annex"],
        )
        for ap in annex_paths[1:50]:
            findings.add("annex", "info", "files", "", "", ap, total=states["annex"])
    if states.get("placeholder") and states.get("placeholder") == nimg:
        findings.add(
            "placeholders",
            "info",
            "files",
            "All image files are zero-byte placeholders",
            "This looks like a skeleton (e.g. bids-examples). Header-derived checks are unavailable.",
        )
    elif states.get("placeholder"):
        findings.add(
            "zero-images",
            "warn",
            "files",
            f"{states['placeholder']} zero-byte image files",
            "Mixed with real images, empty files usually mean an interrupted copy or conversion.",
        )
    if states.get("broken"):
        findings.add(
            "broken-links",
            "warn",
            "files",
            f"{states['broken']} broken symlinks",
            "Targets do not exist.",
        )
    for j in w.junk:
        findings.add(
            "junk",
            "info",
            "files",
            "OS junk files present",
            "e.g. .DS_Store; harmless but noisy.",
            j,
        )
    for nb in nonbids[:50]:
        findings.add(
            "nonbids",
            "warn",
            "naming",
            f"{plural(len(nonbids), 'file')} outside BIDS naming and not in .bidsignore",
            "Validators will reject these unless ignored.",
            nb,
            total=len(nonbids),
        )

    # Subjects/sessions
    if sessions:
        missing_ses = {
            s: sorted(sessions - sub_sessions.get(s, set())) for s in subjects
        }
        for s, miss in missing_ses.items():
            if miss:
                findings.add(
                    "ses-missing",
                    "info",
                    "coverage",
                    "Subjects missing sessions",
                    "Not every subject has every session.",
                    f"sub-{s}: missing ses-{', ses-'.join(miss)}",
                )
        nos = [s for s in subjects if not sub_sessions.get(s)]
        if nos:
            findings.add(
                "ses-mixed",
                "warn",
                "naming",
                "Some subjects have sessions, others do not",
                "Mixing session and session-less layouts complicates every downstream query.",
                ", ".join(f"sub-{s}" for s in nos[:20]),
            )

    # Participants
    model["participants"] = scan_participants(
        root, subjects, findings, participants_mode, is_openneuro, on_evidence
    )

    # Bold metadata and events
    tasks = defaultdict(lambda: {"run_keys": set(), "subjects": set(), "events": set()})
    for r in bold:
        m = r.get("meta", {})
        t = r.get("task") or "(no task)"
        ek = r["key"]  # canonical acquisition key: every entity except echo, part-mag and output entities
        tasks[t]["run_keys"].add(ek)
        tasks[t]["subjects"].add(r["sub"])
        if r.get("echo"):
            tasks[t]["multi_echo"] = True
        if "RepetitionTime" not in m:
            findings.add(
                "no-tr",
                "error",
                "metadata",
                "BOLD runs without RepetitionTime",
                "No TR after resolving inheritance.",
                r["path"],
                unit=ek,
            )
        if "TaskName" not in m:
            findings.add(
                "no-taskname",
                "warn",
                "metadata",
                "BOLD runs without TaskName",
                "Required for task data.",
                r["path"],
                unit=ek,
            )
        tr = fnum(m.get("RepetitionTime"))
        if tr is not None and tr > 20:
            findings.add(
                "tr-ms",
                "error",
                "metadata",
                "RepetitionTime looks like milliseconds",
                f"TR = {tr}; BIDS uses seconds.",
                r["path"],
                unit=ek,
            )
        te = m.get("EchoTime")
        if fnum(te) is not None and fnum(te) > 1:
            findings.add(
                "te-ms",
                "error",
                "metadata",
                "EchoTime looks like milliseconds",
                f"TE = {te}; BIDS uses seconds.",
                r["path"],
                unit=ek,
            )
        if fnum(te) is not None and 0.1 < fnum(te) <= 1:
            findings.add(
                "te-long",
                "warn",
                "metadata",
                "EchoTime implausibly long for BOLD",
                f"TE = {te} s; gradient-echo BOLD is typically 0.015-0.05 s. Check units or the source.",
                sources_of(r, "EchoTime"),
                unit=ek,
            )
        stt = m.get("SliceTiming")
        if isinstance(stt, dict) and stt.get("n") and tr:
            if stt["max"] >= tr:
                sev = "error" if stt["max"] > 5 * tr else "warn"
                findings.add(
                    "st-gt-tr",
                    sev,
                    "metadata",
                    "SliceTiming values reach or exceed TR",
                    "Likely milliseconds or a wrong TR.",
                    r["path"],
                    unit=ek,
                )
        if not m.get("PhaseEncodingDirection"):
            findings.add(
                "no-ped",
                "warn",
                "metadata",
                "BOLD runs without PhaseEncodingDirection",
                "Susceptibility distortion correction needs it.",
                r["path"],
                unit=ek,
            )
        hdr = r.get("hdr")
        if hdr and tr and hdr.get("tr") and abs(hdr["tr"] - tr) > 0.01:
            findings.add(
                "hdr-tr",
                "warn",
                "metadata",
                "Header TR disagrees with sidecar TR",
                f"header {hdr['tr']} s vs sidecar {tr} s",
                r["path"],
                unit=ek,
            )
        ev_rel = events_files.get(ek) or events_files.get(r["key"])
        if ev_rel is None:
            ents = {
                k: r[k]
                for k in ("sub", "ses", "task", "acq", "dir", "run", "echo")
                if r.get(k)
            }
            ev_rel = inh.find(r["path"], ents, "events", ".tsv")
            if ev_rel:
                r["events_inherited"] = True
        r["events_path"] = ev_rel
        if ev_rel:
            ev = summarize_events(root / ev_rel)
            if ev.get("error"):
                empty = ev["error"] == "empty file" or (root / ev_rel).stat().st_size == 0 if (root / ev_rel).exists() else False
                findings.add(
                    "events-empty" if empty else "events-unreadable",
                    "warn",
                    "events",
                    "Empty events.tsv (zero bytes or no rows)" if empty else "Unreadable events.tsv",
                    "Counted as a run without events." if empty else ev["error"],
                    ev_rel,
                    unit=ev_rel,
                )
                r["events_path"] = ev_rel
                r["physio"] = r["key"] in physio
                continue
            r["events"] = ev
            tasks[t]["events"].add(ek)
            if ev.get("issues"):
                findings.add(
                    "events-cols",
                    "error",
                    "events",
                    "events.tsv missing onset/duration",
                    "",
                    ev_rel,
                )
            if ev.get("n_negative"):
                findings.add(
                    "events-neg",
                    "warn",
                    "events",
                    "Negative event onsets",
                    "Events before the first volume.",
                    ev_rel,
                )
            if ev.get("n_na_onset"):
                findings.add(
                    "events-na", "warn", "events", "Events with n/a onset", "", ev_rel
                )
            if ev.get("n") == 0:
                findings.add(
                    "events-empty", "warn", "events", "Empty events.tsv", "", ev_rel
                )
            if ev.get("type_column") is None and ev.get("n"):
                findings.add(
                    "events-notype",
                    "info",
                    "events",
                    "events.tsv without trial_type",
                    "Conditions are shown from the most condition-like column ("
                    + str(ev.get("type_column_inferred") or "none found")
                    + ").",
                    ev_rel,
                )
        r["physio"] = r["key"] in physio
    for t, info in tasks.items():
        info["subjects"] = sorted(info["subjects"])
        info["runs"] = len(info.pop("run_keys"))
        info["events"] = len(info["events"])
        if info["events"] == 0 and "rest" not in t.lower():
            findings.add(
                f"task-noevents-{t}",
                "warn",
                "events",
                f"task-{t} has no events.tsv files",
                "Non-rest task without events; check whether events live elsewhere.",
            )
        elif 0 < info["events"] < info["runs"]:
            seen_noev = set()
            for r in bold:
                if (r.get("task") or "(no task)") != t or r.get("events_path"):
                    continue
                rk = r["key"]
                if rk in seen_noev:
                    continue
                seen_noev.add(rk)
                findings.add(
                    f"task-someevents-{t}",
                    "warn",
                    "events",
                    f"task-{t}: {plural(info['runs'] - info['events'], 'run')} without events.tsv",
                    "Other runs of this task have events; these do not.",
                    r["path"],
                    unit=rk,
                )
    model["tasks"] = {k: v for k, v in sorted(tasks.items())}

    # Parameter consistency per task
    consistency = {}
    for t in tasks:
        echo_files = [r for r in bold if (r.get("task") or "(no task)") == t]
        # Collapse echoes: one entry per acquisition, EchoTime becomes the per-echo tuple.
        grouped: dict[str, list] = defaultdict(list)
        for r in echo_files:
            grouped[r["key"]].append(r)
        runs = []
        for files in grouped.values():
            files = sorted(files, key=lambda r: int(r["echo"]) if str(r.get("echo") or "").isdigit() else 0)
            head = dict(files[0])
            head["meta"] = dict(head.get("meta", {}))
            if len(files) > 1:
                head["meta"]["EchoTime"] = [f.get("meta", {}).get("EchoTime") for f in files]
            runs.append(head)
        params = {}
        for key in (
            "RepetitionTime",
            "PhaseEncodingDirection",
            "EchoTime",
            "MultibandAccelerationFactor",
            "FlipAngle",
            "EffectiveEchoSpacing",
            "TotalReadoutTime",
            "Manufacturer",
            "ManufacturersModelName",
            "MagneticFieldStrength",
        ):
            c = Counter(json.dumps(r.get("meta", {}).get(key)) for r in runs)
            params[key] = [[json.loads(k), v] for k, v in c.most_common()]
        def st_key(r):
            stv = r.get("meta", {}).get("SliceTiming")
            if not stv:
                return "null"
            if not stv["n"]:
                return json.dumps([0, "empty list", "present but []"])
            tr_ = fnum(r["meta"].get("RepetitionTime"))
            # Same severity split as the st-gt-tr finding: > 5 × TR is an error (milliseconds), ≥ TR a warning.
            flag = ("values in ms?" if stv["max"] > 5 * tr_ else "values ≥ TR") if tr_ and stv["max"] >= tr_ else f"max {stv['max']:g} s"
            return json.dumps([stv["n"], stv["order"], flag])

        sl = Counter(st_key(r) for r in runs)
        params["SliceTiming"] = [[json.loads(k), v] for k, v in sl.most_common()]
        nv = Counter(
            r["hdr"]["nvols"] if r.get("hdr") else "header not readable (image not local)"
            for r in runs
        )
        params["Volumes (header)"] = [[k, v] for k, v in nv.most_common()]
        consistency[t] = params
        for key in ("RepetitionTime", "MultibandAccelerationFactor", "Manufacturer"):
            vals = [v for v, _ in params[key] if v is not None]
            if len(vals) > 1:
                majority = params[key][0][0]
                for r in runs:
                    if r.get("meta", {}).get(key) != majority:
                        findings.add(
                            f"hetero-{t}-{key}",
                            "warn",
                            "consistency",
                            f"task-{t}: {key} varies across runs",
                            "Values: " + ", ".join(f"{v} (×{n})" for v, n in params[key])
                            + ". Listed: runs that differ from the majority.",
                            f"{r['path']}: {key} = {r.get('meta', {}).get(key)} (majority {majority})",
                            unit=r["path"],
                        )
        peds = [v for v, _ in params["PhaseEncodingDirection"] if v is not None]
        if len(peds) > 1:
            findings.add(
                f"hetero-{t}-ped",
                "info",
                "consistency",
                f"task-{t}: mixed PhaseEncodingDirection",
                "Often intentional (blip-up/down runs); confirm.",
                None,
            )
    model["consistency"] = consistency

    # Missing runs relative to modal run set per task/session
    by_cell = defaultdict(set)
    for r in bold:
        by_cell[(r["sub"], r.get("ses"), r.get("task"))].add(
            (r.get("acq"), r.get("dir"), r.get("run"), r.get("echo"))
        )
    modal = defaultdict(Counter)
    for (s, ses, t), runs in by_cell.items():
        modal[(ses, t)][len(runs)] += 1
    for (s, ses, t), runs in by_cell.items():
        mode_n = modal[(ses, t)].most_common(1)[0][0]
        if len(runs) < mode_n:
            findings.add(
                "fewer-runs",
                "warn",
                "coverage",
                "Subjects with fewer BOLD runs than typical",
                "Compared with the most common run count for the same task and session.",
                f"sub-{s}{' ses-' + ses if ses else ''} task-{t}: {len(runs)} vs {mode_n}",
            )
        elif len(runs) > mode_n:
            findings.add(
                "more-runs",
                "info",
                "coverage",
                "Subjects with extra BOLD runs",
                "Possibly repeated runs after a problem; check scans.tsv or notes.",
                f"sub-{s}{' ses-' + ses if ses else ''} task-{t}: {len(runs)} vs {mode_n}",
            )
    for t in tasks:
        missing = sorted(set(subjects) - set(tasks[t]["subjects"]))
        if missing and len(missing) < len(subjects):
            findings.add(
                f"task-missing-{t}",
                "warn",
                "coverage",
                f"task-{t} absent for {len(missing)} subjects",
                "",
                ", ".join(f"sub-{s}" for s in missing[:30]),
            )

    # Fieldmaps
    bold_paths = {r["path"]: r for r in bold}
    covered = defaultdict(list)
    for fm in fmap:
        for it in fm.get("intended_for", []):
            itp = str(it)
            if itp.startswith("bids::"):
                target = itp[len("bids::") :]
            else:
                target = f"sub-{fm['sub']}/{itp}"
            if target not in file_index:
                findings.add(
                    "intendedfor-missing",
                    "warn",
                    "fmap",
                    "IntendedFor targets that do not exist",
                    "Fieldmaps will not be applied to these runs.",
                    f"{fm['path']} → {itp}",
                )
            else:
                covered[target].append(fm["path"])
    b0src = {r["path"] for r in bold if r.get("meta", {}).get("B0FieldSource")}
    for r in bold:
        r["fmaps"] = covered.get(r["path"], [])
        r["b0_source"] = r.get("meta", {}).get("B0FieldSource")
    if fmap:
        unc = [r["path"] for r in bold if not r["fmaps"] and r["path"] not in b0src]
        for p in unc:
            findings.add(
                "bold-nofmap",
                "warn",
                "fmap",
                "BOLD runs with no fieldmap (IntendedFor or B0FieldSource)",
                "Dataset has fieldmaps, but these runs are not targeted by any.",
                p,
            )
    model["bold"] = bold
    model["anat"] = anat
    model["dwi"] = dwi
    model["fmap"] = fmap
    model["other_func"] = other_runs
    model["scans_tsv"] = scans_tsv

    # Derivatives
    derivs = []
    droots = [(root.name, root)] if is_deriv_root else []
    ddir = root / "derivatives"
    if ddir.is_dir():
        for p in sorted(ddir.iterdir()):
            if p.is_dir() and p.name not in SKIP_DIRS:
                droots.append((f"derivatives/{p.name}", p))
    seen_roots = {q.resolve() for _, q in droots}
    for p in extra_derivs or []:
        p = p.resolve()
        if p in seen_roots:
            continue
        seen_roots.add(p)
        label = p.name if p.name not in {lab for lab, _ in droots} else f"{p.parent.name}/{p.name}"
        droots.append((label, p))
    raw_keys = {r["key"]: r for r in bold}
    raw_keys_noecho = {r["key"]: r for r in bold}
    for label, p in droots:
        d = scan_derivative(p, label, findings)
        d["abs_root"] = str(p.resolve())
        # Nested pipelines (e.g. derivatives/fmriprep/freesurfer) are counted but not deep-scanned.
        derivs.append(d)
    for d in derivs:
        if not d["confounds"]:
            continue
        finalize_traces(d["confounds"])
        seen = set()
        for c in d["confounds"]:
            rr = raw_keys_noecho.get(c["key"])
            seen.add(c["key"])
            c["raw"] = rr["path"] if rr else None
            if rr is None and bold:
                findings.add(
                    f"conf-noraw-{d['label']}",
                    "warn",
                    "derivatives",
                    f"{d['label']}: confounds with no matching raw BOLD run",
                    "Derivative and raw datasets disagree, or raw is from a different version.",
                    c["path"],
                )
            if c.get("state") != "present":
                findings.add(
                    f"conf-absent-{d['label']}",
                    "info",
                    "derivatives",
                    f"{d['label']}: confounds files not fetched",
                    "Annexed or empty; QC metrics unavailable for these runs.",
                    c["path"],
                )
                continue
            if c.get("error"):
                findings.add(
                    "conf-unreadable",
                    "error",
                    "derivatives",
                    "Unreadable confounds files",
                    c["error"],
                    c["path"],
                )
                continue
            if rr is not None:
                nv = (rr.get("hdr") or {}).get("nvols")
                if nv and c.get("n_vols") and nv != c["n_vols"]:
                    findings.add(
                        "conf-nvols",
                        "error",
                        "derivatives",
                        "Confounds rows ≠ BOLD volumes",
                        f"{c['n_vols']} rows vs {nv} volumes.",
                        c["path"],
                    )
            if c.get("ragged_rows"):
                findings.add(
                    "conf-ragged",
                    "error",
                    "derivatives",
                    "Confounds files with ragged rows",
                    "",
                    c["path"],
                )
            fd = c.get("fd") or {}
            if fd.get("mean") is not None and fd["mean"] > 0.5:
                findings.add(
                    f"high-motion-{d['label']}",
                    "warn",
                    "motion",
                    f"{d['label']}: runs with mean FD > 0.5 mm",
                    "Candidates for exclusion; adjust the threshold in the Motion view.",
                    c["path"],
                )
        if bold:
            missing = sorted({k for k in raw_keys_noecho} - seen)
            for k in missing:
                findings.add(
                    f"conf-missing-{d['label']}",
                    "warn",
                    "derivatives",
                    f"{d['label']}: raw BOLD runs with no confounds",
                    "Preprocessing skipped or failed for these.",
                    k,
                )
        namings = Counter(c.get("naming") for c in d["confounds"] if c.get("naming"))
        if len(namings) > 1:
            findings.add(
                f"conf-naming-{d['label']}",
                "warn",
                "derivatives",
                f"{d['label']}: mixed confound naming conventions",
                "Files from different fMRIPrep generations.",
                None,
            )
        d["naming"] = dict(namings)
    model["derivatives"] = derivs
    scan_lengths(bold, derivs, findings)
    if not bold and not derivs:
        findings.add(
            "no-bold",
            "info",
            "dataset",
            "No BOLD runs found",
            "This dashboard is fMRI-centric; other datatypes are summarized only.",
        )
    model["findings"] = findings.list()
    return model


def slice_order(vals: list[float]) -> str:
    n = len(vals)
    if n < 3:
        return "n/a"
    uniq = sorted(set(vals))
    if len(uniq) < n:
        mb = n // len(uniq) if len(uniq) else 1
        prefix = f"multiband×{mb} "
        vals = (
            vals[: len(uniq)]
            if all(vals[i] == vals[i % len(uniq)] for i in range(n))
            else vals
        )
    else:
        prefix = ""
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    if order == list(range(len(vals))):
        return prefix + "ascending"
    if order == list(range(len(vals)))[::-1]:
        return prefix + "descending"
    evens = list(range(0, len(vals), 2)) + list(range(1, len(vals), 2))
    odds = list(range(1, len(vals), 2)) + list(range(0, len(vals), 2))
    if order == evens or order == odds:
        return prefix + "interleaved"
    return prefix + "other"


def scan_participants(
    root: Path,
    subjects: set,
    findings: Findings,
    mode: str,
    is_openneuro: bool,
    evidence: str = "",
):
    p = root / "participants.tsv"
    out = {
        "present": p.exists(),
        "included": False,
        "reason": "",
        "columns": [],
        "summary": {},
        "rows": [],
    }
    if not p.exists():
        if subjects:
            findings.add(
                "participants-missing",
                "warn",
                "participants",
                "No participants.tsv",
                "Recommended by BIDS.",
            )
        return out
    header, rows, err = read_tsv(p)
    if err or not header:
        findings.add(
            "participants-bad",
            "error",
            "participants",
            "participants.tsv unreadable",
            err or "",
            "participants.tsv",
        )
        return out
    out["columns"] = header
    if header[0] != "participant_id":
        findings.add(
            "participants-col",
            "error",
            "participants",
            "participants.tsv first column is not participant_id",
            f"Found {header[0]!r}.",
            "participants.tsv",
        )
    ids = [r[0].strip() for r in rows if r]
    listed = {i[4:] if i.startswith("sub-") else i for i in ids}
    bad_prefix = [i for i in ids if not i.startswith("sub-")]
    if bad_prefix:
        findings.add(
            "participants-prefix",
            "warn",
            "participants",
            "participant_id values without 'sub-' prefix",
            "",
            ", ".join(bad_prefix[:10]),
        )
    dup = [i for i, n in Counter(ids).items() if n > 1]
    if dup:
        findings.add(
            "participants-dup",
            "error",
            "participants",
            "Duplicate participant_id rows",
            "",
            ", ".join(dup[:10]),
        )
    for s in sorted(subjects - listed):
        findings.add(
            "participants-notlisted",
            "warn",
            "participants",
            "Subjects on disk but not in participants.tsv",
            "",
            f"sub-{s}",
        )
    for s in sorted(listed - subjects):
        findings.add(
            "participants-nodata",
            "info",
            "participants",
            "participants.tsv rows with no subject folder",
            "",
            f"sub-{s}",
        )
    out["n_rows"] = len(rows)
    out["listed_not_on_disk"] = sorted(listed - subjects)
    out["on_disk_not_listed"] = sorted(subjects - listed)
    include = mode == "yes" or (mode == "auto" and is_openneuro)
    out["included"] = include
    out["reason"] = {"yes": "included by request", "no": "withheld by request"}.get(
        mode,
        f"public OpenNeuro dataset ({evidence})"
        if is_openneuro
        else f"{evidence[:1].upper() + evidence[1:]}. Rebuild with --participants yes once the data are "
        "confirmed de-identified or the page stays on an internal machine.",
    )
    # Column-level summaries: types and missingness are shown even when values are withheld.
    for j, c in enumerate(header):
        vals = [r[j].strip() if j < len(r) else "" for r in rows]
        na = sum(1 for v in vals if v in ("", "n/a", "NA", "N/A"))
        nums = [fnum(v) for v in vals]
        numeric = [v for v in nums if v is not None]
        s = {"n": len(vals), "na": na}
        if j == 0:
            s["type"] = "id"
        elif (
            numeric and len(numeric) >= 0.8 * (len(vals) - na) and len(set(numeric)) > 5
        ):
            s["type"] = "numeric"
            if include:
                st = stats(numeric)
                s.update({k: rnd(v, 3) for k, v in st.items()})
                s["values"] = [rnd(v, 3) for v in numeric]
        else:
            s["type"] = "categorical"
            if include:
                s["levels"] = dict(
                    Counter(v for v in vals if v not in ("", "n/a")).most_common(12)
                )
                s["n_levels"] = len(set(vals))
        out["summary"][c] = s
    if include:
        out["rows"] = rows[:5000]
    if (root / "participants.json").exists():
        pj, perr = read_json(root / "participants.json")
        out["dictionary"] = pj if isinstance(pj, dict) else None
        if isinstance(pj, dict):
            undoc = [c for c in header[1:] if c not in pj]
            if undoc:
                findings.add(
                    "participants-undoc",
                    "info",
                    "participants",
                    "participants.tsv columns without a data dictionary entry",
                    "Add them to participants.json.",
                    ", ".join(undoc[:20]),
                )
    return out


# ----------------------------------------------------------------------------- render


def load_findings(path: Path) -> list:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("findings", [])
    if not isinstance(data, list):
        raise SystemExit(f"{path}: expected a list of findings or {{\"findings\": [...]}}")
    return data


def merge_findings(model: dict, extra: list | None):
    if not extra:
        return model
    seen = {f["id"] for f in model["findings"]}
    for f in extra:
        if not isinstance(f, dict) or "title" not in f:
            continue
        f = {
            "severity": "info",
            "category": "review",
            "detail": "",
            "paths": [],
            "count": 1,
            **f,
            "source": "agent",
        }
        if f.get("id") in seen:
            f["id"] = f"agent-{f['id']}"
        model["findings"].append(f)
    return model


def render(model: dict, out: Path, template: Path = TEMPLATE):
    html = template.read_text(encoding="utf-8")
    payload = json.dumps(
        model, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )
    payload = payload.replace("</", "<\\/").replace("<!--", "<\\!--")
    marker = "/*__BIDS_ATLAS_DATA__*/null"
    if marker not in html:
        raise SystemExit(f"template lacks data marker: {template}")
    html = html.replace(marker, payload, 1)
    title = (
        (model.get("description") or {}).get("Name")
        or model.get("root_name")
        or "BIDS dataset"
    )
    html = html.replace("__BIDS_ATLAS_TITLE__", _esc(str(title))[:120], 1)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def relink(model: dict, root: Path, out: Path):
    """Make report/figure links relative to where the HTML will live."""
    base = out.resolve().parent
    for d in model.get("derivatives", []):
        droot = Path(d.pop("abs_root")) if d.get("abs_root") else None
        if droot is None:
            continue
        d["report_links"] = {
            r: os.path.relpath(droot / r, base)
            for r in d.get("reports", []) + d.get("group_reports", [])
        }
    model["link_base"] = os.path.relpath(root, base)


def _clean_nan(o):
    if isinstance(o, float) and not math.isfinite(o):
        return None
    if isinstance(o, dict):
        return {k: _clean_nan(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_clean_nan(v) for v in o]
    return o


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("scan", "build"):
        sp = sub.add_parser(name)
        sp.add_argument("root", type=Path)
        sp.add_argument(
            "--derivatives",
            type=Path,
            action="append",
            default=[],
            help="extra derivative roots outside ROOT/derivatives (repeatable)",
        )
        sp.add_argument(
            "--participants",
            choices=("auto", "yes", "no"),
            default="auto",
            help="include participants.tsv values: auto = only for OpenNeuro datasets",
        )
        sp.add_argument("-o", "--out", type=Path, required=True)
        if name == "build":
            sp.add_argument("--findings", type=Path)
            sp.add_argument("--model-out", type=Path)
    rp = sub.add_parser("render")
    rp.add_argument("model", type=Path)
    rp.add_argument("--findings", type=Path)
    rp.add_argument("-o", "--out", type=Path, required=True)
    a = ap.parse_args(argv)

    if a.cmd in ("scan", "build"):
        if not a.root.is_dir():
            ap.error(f"not a directory: {a.root}")
        for p in a.derivatives:
            if not p.is_dir():
                ap.error(f"derivatives path is not a directory: {p}")
        model = scan(a.root, a.derivatives, a.participants)
        # remember extra-derivative absolute roots for link rewriting
        model = _clean_nan(model)
        if a.cmd == "scan":
            relink(model, a.root.resolve(), a.out)
            a.out.parent.mkdir(parents=True, exist_ok=True)
            a.out.write_text(
                json.dumps(model, indent=1, ensure_ascii=True), encoding="utf-8"
            )
            print(f"wrote {a.out} ({len(model['findings'])} finding groups)")
            return 0
        relink(model, a.root.resolve(), a.out)
        if a.model_out:
            a.model_out.parent.mkdir(parents=True, exist_ok=True)
            a.model_out.write_text(
                json.dumps(model, indent=1, ensure_ascii=True), encoding="utf-8"
            )
        extra = load_findings(a.findings) if a.findings else None
        render(merge_findings(model, extra), a.out)
        print(f"wrote {a.out}")
        return 0
    model = json.loads(a.model.read_text(encoding="utf-8"))
    extra = load_findings(a.findings) if a.findings else None
    render(merge_findings(model, extra), a.out)
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
