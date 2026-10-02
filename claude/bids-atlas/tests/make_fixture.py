#!/usr/bin/env python3
"""Build a synthetic BIDS + fMRIPrep dataset with planted oddities.

    python make_fixture.py OUTDIR

Returns (via build()) the finding ids the scanner must report. Images are tiny
NIfTI headers (no voxel data) so header-derived checks can run.
"""
from __future__ import annotations

import gzip
import json
import math
import os
import random
import struct
import sys
from pathlib import Path

TASKS = {
    "nback": {"runs": 2, "tr": 2.0, "nvols": 180},
    "rest": {"runs": 1, "tr": 2.0, "nvols": 240},
}
SUBJECTS = ["01", "02", "03", "04", "05", "06", "07", "08"]
SESSIONS = ["1", "2"]


def nifti(path: Path, nvols: int, tr: float):
    """A valid NIfTI-1 header (no data) - enough for dim/pixdim checks."""
    hdr = bytearray(348)
    struct.pack_into("<i", hdr, 0, 348)
    struct.pack_into("<8h", hdr, 40, 4, 64, 64, 36, nvols, 1, 1, 1)
    struct.pack_into("<h", hdr, 70, 16)  # datatype float32
    struct.pack_into("<8f", hdr, 76, 1.0, 3.0, 3.0, 3.5, tr, 0, 0, 0)
    hdr[123] = 2 | 8  # mm + sec
    hdr[344:348] = b"n+1\0"
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb") as fh:
        fh.write(bytes(hdr) + b"\0\0\0\0")


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def jdump(path: Path, obj):
    write(path, json.dumps(obj, indent=2))


def slice_times(n=36, tr=2.0, ms=False):
    order = list(range(0, n, 2)) + list(range(1, n, 2))
    t = [0.0] * n
    for k, i in enumerate(order):
        t[i] = round(k * tr / n, 4)
    return [round(x * 1000, 1) for x in t] if ms else t


def confounds(rng: random.Random, n: int, motion: float, spikes: int):
    cols = [
        "global_signal",
        "csf",
        "white_matter",
        "std_dvars",
        "dvars",
        "framewise_displacement",
        "rmsd",
    ]
    cols += [
        f"{a}{s}"
        for a in ("trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z")
        for s in ("", "_derivative1", "_power2", "_derivative1_power2")
    ]
    cols += (
        [f"cosine{i:02d}" for i in range(4)]
        + [f"a_comp_cor_{i:02d}" for i in range(10)]
        + [f"t_comp_cor_{i:02d}" for i in range(4)]
    )
    cols += ["non_steady_state_outlier00"]
    pos = [0.0] * 6
    rows = []
    spike_at = set(rng.sample(range(5, n), spikes)) if spikes else set()
    fds = []
    for t in range(n):
        step = [rng.gauss(0, motion * (6 if t in spike_at else 1)) for _ in range(6)]
        step[3:] = [s / 50 for s in step[3:]]
        pos = [p + s for p, s in zip(pos, step)]
        fd = (
            None
            if t == 0
            else sum(abs(s) for s in step[:3]) + 50 * sum(abs(s) for s in step[3:])
        )
        fds.append(fd)
        dv = None if t == 0 else max(0.6, rng.gauss(1.0, 0.12) + (fd or 0) * 1.4)
        row = {
            "global_signal": 500 + rng.gauss(0, 3),
            "csf": 600 + rng.gauss(0, 5),
            "white_matter": 520 + rng.gauss(0, 2),
            "std_dvars": dv,
            "dvars": None if dv is None else dv * 18,
            "framewise_displacement": fd,
            "rmsd": fd and fd * 0.4,
        }
        for i, a in enumerate(
            ("trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z")
        ):
            row[a] = pos[i]
            row[a + "_power2"] = pos[i] ** 2
            row[a + "_derivative1"] = None if t == 0 else step[i]
            row[a + "_derivative1_power2"] = None if t == 0 else step[i] ** 2
        for i in range(4):
            row[f"cosine{i:02d}"] = math.cos(math.pi * (i + 1) * (t + 0.5) / n)
        for i in range(10):
            row[f"a_comp_cor_{i:02d}"] = rng.gauss(0, 0.05)
        for i in range(4):
            row[f"t_comp_cor_{i:02d}"] = rng.gauss(0, 0.05)
        row["non_steady_state_outlier00"] = 1 if t == 0 else 0
        rows.append(row)
    fmt = (
        lambda v: "n/a"
        if v is None
        else (f"{v:.6g}" if isinstance(v, float) else str(v))
    )
    tsv = (
        "\t".join(cols)
        + "\n"
        + "\n".join("\t".join(fmt(r[c]) for c in cols) for r in rows)
        + "\n"
    )
    meta = {}
    ve = [0.21, 0.12, 0.08, 0.06, 0.05, 0.04, 0.035, 0.03, 0.02, 0.015]
    cum = 0
    for i, v in enumerate(ve):
        cum += v
        meta[f"a_comp_cor_{i:02d}"] = {
            "Method": "aCompCor",
            "Mask": "combined",
            "Retained": True,
            "SingularValue": 30 - i,
            "VarianceExplained": v,
            "CumulativeVarianceExplained": round(cum, 4),
        }
    for i in range(4):
        meta[f"t_comp_cor_{i:02d}"] = {
            "Method": "tCompCor",
            "Retained": True,
            "VarianceExplained": 0.1 - 0.02 * i,
            "CumulativeVarianceExplained": round(
                sum(0.1 - 0.02 * k for k in range(i + 1)), 4
            ),
        }
    meta["dropped_0"] = {
        "Method": "aCompCor",
        "Mask": "combined",
        "Retained": False,
        "VarianceExplained": 0.004,
    }
    return tsv, meta


def events(rng, tr, nvols, past_end=False, negative=False):
    lines = ["onset\tduration\ttrial_type\tresponse_time"]
    t = -1.5 if negative else 8.0
    end = tr * nvols
    kinds = ["0back", "2back", "fixation"]
    i = 0
    while t < end - 30:
        k = kinds[i % 3]
        lines.append(
            f"{t:.2f}\t{20 if k != 'fixation' else 10}\t{k}\t{rng.uniform(0.4, 1.1):.3f}"
        )
        t += 30 if k != "fixation" else 14
        i += 1
    if past_end:
        lines.append(f"{end + 6:.2f}\t12\t2back\tn/a")
    return "\n".join(lines) + "\n"


def build(root: Path) -> set[str]:
    rng = random.Random(42)
    root.mkdir(parents=True, exist_ok=True)
    jdump(
        root / "dataset_description.json",
        {
            "Name": "Synthetic messy n-back study",
            "BIDSVersion": "1.9.0",
            "DatasetType": "raw",
            "Authors": ["A. Researcher", "B. Analyst"],
            "License": "CC0",
        },
    )
    write(
        root / "README",
        "Synthetic dataset for bids-atlas tests. Every oddity is planted.\n",
    )
    write(
        root / "participants.tsv",
        "participant_id\tage\tsex\tgroup\n"
        + "".join(
            f"sub-{s}\t{rng.randint(19, 34)}\t{rng.choice('MF')}\t{'patient' if int(s) % 2 else 'control'}\n"
            for s in SUBJECTS
            if s != "08"
        )
        + "sub-09\t25\tF\tcontrol\n",
    )
    jdump(
        root / "participants.json",
        {
            "age": {"Description": "age", "Units": "years"},
            "sex": {"Description": "sex"},
        },
    )
    jdump(
        root / "task-nback_bold.json",
        {
            "TaskName": "nback",
            "RepetitionTime": 2.0,
            "EchoTime": 0.03,
            "PhaseEncodingDirection": "j-",
            "SliceTiming": slice_times(),
            "MultibandAccelerationFactor": 1,
            "Manufacturer": "Siemens",
        },
    )
    jdump(
        root / "task-rest_bold.json",
        {
            "TaskName": "rest",
            "RepetitionTime": 2.0,
            "EchoTime": 0.03,
            "PhaseEncodingDirection": "j-",
            "SliceTiming": slice_times(),
            "Manufacturer": "Siemens",
        },
    )
    write(root / ".DS_Store", "x")
    prep = root / "derivatives" / "fmriprep"
    jdump(
        prep / "dataset_description.json",
        {
            "Name": "fMRIPrep - fMRI PREProcessing workflow",
            "BIDSVersion": "1.4.0",
            "DatasetType": "derivative",
            "GeneratedBy": [{"Name": "fMRIPrep", "Version": "23.2.1"}],
        },
    )
    write(
        prep / "logs" / "CITATION.md",
        "Results included in this manuscript come from preprocessing performed using *fMRIPrep* 23.2.1.\n",
    )
    for s in SUBJECTS:
        sessions = SESSIONS if s != "05" else ["1"]  # planted: missing session
        write(prep / f"sub-{s}.html", "<html><body>report</body></html>")
        for ses in sessions:
            base = root / f"sub-{s}" / f"ses-{ses}"
            nifti(base / "anat" / f"sub-{s}_ses-{ses}_T1w.nii.gz", 1, 0)
            jdump(
                base / "anat" / f"sub-{s}_ses-{ses}_T1w.json",
                {"RepetitionTime": 2.3, "EchoTime": 0.00298, "InversionTime": 0.9},
            )
            intended = []
            for task, spec in TASKS.items():
                nruns = spec["runs"] - (
                    1 if s == "04" and task == "nback" and ses == "2" else 0
                )  # planted: missing run
                for r in range(1, nruns + 1):
                    stem = f"sub-{s}_ses-{ses}_task-{task}_run-{r}"
                    nv = spec["nvols"]
                    nifti(base / "func" / f"{stem}_bold.nii.gz", nv, spec["tr"])
                    side = {}
                    if s == "03" and task == "nback":
                        side["RepetitionTime"] = 2.5  # planted: TR heterogeneity
                    if s == "06" and task == "rest":
                        side["EchoTime"] = 30  # planted: TE in ms
                    if s == "07" and task == "nback" and ses == "1":
                        side["SliceTiming"] = slice_times(
                            ms=True
                        )  # planted: slice timing in ms
                    if s == "02" and task == "rest" and ses == "2":
                        side["MultibandAcclerationFactor"] = 4  # planted: typo
                    if side:
                        jdump(base / "func" / f"{stem}_bold.json", side)
                    if task == "nback":
                        write(
                            base / "func" / f"{stem}_events.tsv",
                            events(
                                rng,
                                spec["tr"],
                                nv,
                                past_end=(s == "02" and r == 2),
                                negative=(s == "08" and ses == "1" and r == 1),
                            ),
                        )
                    if not (s == "01" and ses == "2"):
                        intended.append(
                            f"bids::sub-{s}/ses-{ses}/func/{stem}_bold.nii.gz"
                        )
                    # derivatives
                    if s == "07" and ses == "2" and task == "rest":
                        continue  # planted: preprocessing missing
                    motion = 0.03 if s != "06" else 0.09  # planted: high-motion subject
                    nrows = (
                        nv
                        if not (s == "02" and task == "rest" and ses == "1")
                        else nv - 4
                    )  # planted: row mismatch
                    tsv, meta = confounds(
                        rng, nrows, motion, spikes=3 if s != "06" else 20
                    )
                    write(
                        prep
                        / f"sub-{s}"
                        / f"ses-{ses}"
                        / "func"
                        / f"{stem}_desc-confounds_timeseries.tsv",
                        tsv,
                    )
                    jdump(
                        prep
                        / f"sub-{s}"
                        / f"ses-{ses}"
                        / "func"
                        / f"{stem}_desc-confounds_timeseries.json",
                        meta,
                    )
            fm = {
                "PhaseEncodingDirection": "j",
                "TotalReadoutTime": 0.05,
                "IntendedFor": intended,
            }
            if s == "03":
                fm["IntendedFor"] = intended + [
                    f"bids::sub-{s}/ses-{ses}/func/sub-{s}_ses-{ses}_task-nback_run-9_bold.nii.gz"
                ]  # planted
            jdump(base / "fmap" / f"sub-{s}_ses-{ses}_dir-PA_epi.json", fm)
            nifti(base / "fmap" / f"sub-{s}_ses-{ses}_dir-PA_epi.nii.gz", 3, 0)
    # planted: invalid JSON and stray file
    write(
        root / "sub-01" / "ses-1" / "func" / "sub-01_ses-1_task-nback_run-1_bold.json",
        '{"FlipAngle": 52,}',
    )
    write(root / "sub-01" / "ses-1" / "func" / "notes.txt", "scanner hiccup\n")
    # planted: derivative-only run (no raw)
    tsv, meta = confounds(rng, 120, 0.03, 1)
    write(
        prep
        / "sub-01"
        / "ses-1"
        / "func"
        / "sub-01_ses-1_task-localizer_run-1_desc-confounds_timeseries.tsv",
        tsv,
    )
    # planted: un-fetched annex link
    link = root / "sub-08" / "ses-2" / "anat" / "sub-08_ses-2_T2w.nii.gz"
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(
            "../../../.git/annex/objects/XX/YY/SHA256E-s1--abc.nii.gz/SHA256E-s1--abc.nii.gz",
            link,
        )
    except OSError:
        pass
    return {
        "json-invalid",
        "nonbids",
        "junk",
        "hetero-nback-RepetitionTime",
        "te-ms",
        "st-gt-tr",
        "typo-MultibandAcclerationFactor",
        "events-past-end",
        "events-neg",
        "fewer-runs",
        "ses-missing",
        "participants-notlisted",
        "participants-nodata",
        "intendedfor-missing",
        "bold-nofmap",
        "conf-nvols",
        "high-motion-derivatives/fmriprep",
        "conf-missing-derivatives/fmriprep",
        "conf-noraw-derivatives/fmriprep",
        "annex",
    }


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "messy")
    expected = build(out)
    print(f"built {out} with {len(expected)} planted findings")
