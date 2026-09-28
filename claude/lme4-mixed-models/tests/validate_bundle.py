#!/usr/bin/env python3
"""Static/package/algebra checks. This deliberately does NOT claim to parse or run R."""
from pathlib import Path
import argparse
from datetime import date, datetime, timezone
import json
import math
import re
import shutil
from urllib.parse import urlparse
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, help="Optionally save this run's JSON receipt; stdout is always emitted")
args = parser.parse_args()
checks = []

def check(name, fn):
    try:
        details = fn()
        checks.append({"name": name, "status": "PASS", "details": details})
    except Exception as exc:
        checks.append({"name": name, "status": "FAIL", "details": str(exc)})

def require(condition, message):
    if not condition:
        raise AssertionError(message)

sources = json.loads((ROOT / "references/sources.json").read_text())
ids = {s["id"] for s in sources}


def source_registry():
    require(len(ids) == len(sources), "Duplicate source IDs")
    required = {"id", "author", "title", "year", "kind", "url", "accessed", "access_scope", "use", "limitation"}
    for s in sources:
        require(required.issubset(s), f"Incomplete source {s}")
        u = urlparse(s["url"])
        require(u.scheme == "https" and bool(u.netloc), f"Invalid URL: {s['id']}")
        require(date.fromisoformat(s["accessed"]).isoformat() == s["accessed"],
                f"Invalid ISO access date: {s['id']}")
    return f"{len(sources)} unique, scoped source entries. URL syntax checked; no live link crawler was run."
check("source_registry", source_registry)


def frontmatter():
    text = (ROOT / "SKILL.md").read_text()
    parts = text.split("---", 2)
    require(len(parts) == 3 and not parts[0].strip(), "Missing YAML frontmatter")
    obj = yaml.safe_load(parts[1])
    require(obj["name"] == "lme4-mixed-models", "Wrong skill name")
    require(0 < len(obj["description"]) <= 1024, "Description missing or oversized")
    require(set(obj) == {"name", "description"}, "Unexpected vendor-specific metadata")
    words = len(text.split())
    require(words < 1600, "Core too large for stated word budget")
    return {"core_word_count": words, "frontmatter_keys": sorted(obj)}
check("portable_frontmatter_and_core_budget", frontmatter)


def local_links():
    n = 0
    for p in ROOT.rglob("*.md"):
        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", p.read_text()):
            if urlparse(link).scheme or link.startswith("#"):
                continue
            target = link.split("#", 1)[0]
            require((p.parent / target).exists(), f"Broken link {p.relative_to(ROOT)} -> {link}")
            n += 1
    return f"{n} relative Markdown links resolve."
check("relative_markdown_links", local_links)


def citation_ids():
    used = set()
    for p in ROOT.rglob("*.md"):
        for group in re.findall(r"\[([A-Z][A-Z0-9-]*(?:;\s*[A-Z][A-Z0-9-]*)*)\](?!\()", p.read_text()):
            for sid in re.split(r";\s*", group):
                require(sid in ids, f"Unknown citation ID {sid} in {p}")
                used.add(sid)
    return {"referenced_source_ids": len(used), "registered_source_ids": len(ids)}
check("citation_id_resolution", citation_ids)


def yaml_contracts():
    plan = yaml.safe_load((ROOT / "templates/analysis-plan.yml").read_text())
    require(plan["status"] == "NEEDS_DESIGN", "Plan should begin unresolved")
    ev = yaml.safe_load((ROOT / "evals/scenarios.yml").read_text())
    require(ev["status"] == "specified_not_executed", "Do not label unrun evaluations passed")
    cases = ev["cases"]
    require(len({c["id"] for c in cases}) == len(cases), "Duplicate eval case")
    for c in cases:
        require(all(k in c for k in ("id", "prompt", "must", "must_not", "sources")), "Incomplete case")
        require(set(c["sources"]).issubset(ids), f"Unknown eval sources for {c['id']}")
    return f"Analysis plan and {len(cases)} behavioral specifications parsed; evaluations NOT executed."
check("yaml_contracts_and_eval_specs", yaml_contracts)


def r_delimiters():
    count = 0
    for p in ROOT.rglob("*.R"):
        text = p.read_text()
        stack = []
        quote = None
        escaped = False
        comment = False
        line = 1
        for ch in text:
            if ch == "\n":
                line += 1
                comment = False
            if comment:
                continue
            if quote:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == quote:
                    quote = None
                continue
            if ch == "#":
                comment = True
            elif ch in "\"'`":
                quote = ch
            elif ch in "([{":
                stack.append((ch, line))
            elif ch in ")]}":
                require(bool(stack), f"Unmatched {ch}: {p}:{line}")
                expected = {')': '(', ']': '[', '}': '{'}[ch]
                found, start = stack.pop()
                require(found == expected, f"Mismatched delimiters {p}:{start}-{line}")
        require(not quote and not stack, f"Unclosed quote/delimiter in {p}")
        count += 1
    return f"Balanced delimiters/quoted strings in {count} R files; NOT an R parser/runtime check."
check("R_lexical_delimiter_check_only", r_delimiters)


def core_guardrails():
    text = (ROOT / "SKILL.md").read_text()
    expected = ["NEEDS_DESIGN", "NUMERICAL_UNRESOLVED", "SINGULAR_REVIEW", "READY_WITH_LIMITS",
                "isSingular", "rePCA", "maxeval", "maxfun", "Satterthwaite", "Kenward",
                "re.form=NA", "crossed", "nAGQ=1", "multiplicity", "selection"]
    for phrase in expected:
        require(phrase in text, f"Missing core routing/guardrail phrase: {phrase}")
    return f"{len(expected)} critical concepts present. Presence is not a behavioral success test."
check("core_guardrail_presence", core_guardrails)


def covariance_centering():
    G = np.diag([4., 1.])
    c = 3.
    T = np.array([[1., c], [0., 1.]])
    Gc = T @ G @ T.T
    require(np.isclose(Gc[0, 1], c * G[1, 1]), "Covariance identity failed")
    require(not np.isclose(Gc[0, 1], 0), "Constraint wrongly preserved")
    return {"old_covariance": 0., "new_covariance": float(Gc[0, 1])}
check("derived_centering_changes_diagonal_constraint", covariance_centering)


def full_basis_invariance():
    G = np.array([[4., .3], [.3, 1.]])
    c = 2.5
    T = np.array([[1., c], [0., 1.]])
    Gc = T @ G @ T.T
    for x in (-2., 0., 4.):
        z = np.array([1., x]); zc = np.array([1., x-c])
        require(np.isclose(z @ G @ z, zc @ Gc @ zc), "Full covariance reparameterization failed")
    return "Random-contribution variance invariant under the matching full covariance transformation."
check("derived_full_covariance_basis_invariance", full_basis_invariance)


def binary_coding():
    beta = 2.7
    require(np.isclose(beta * (.5 - (-.5)), beta), "Half coding failed")
    require(np.isclose(beta * (1 - (-1)), 2 * beta), "Sum coding failed")
    return "Binary contrast scale identities verified."
check("derived_binary_contrast_scaling", binary_coding)

# Independent Python quadrature checks; these do not execute the shipped R helper.
z, w = np.polynomial.hermite.hermgauss(80)
w = w / np.sqrt(np.pi)
u = np.sqrt(2.) * z
logistic = lambda x: 1. / (1. + np.exp(-x))


def nonlinear_mean():
    at_zero = float(logistic(2.))
    marginal = float(np.dot(w, logistic(2. + u)))
    require(marginal < at_zero and abs(marginal - at_zero) > .01, "Distinct GLMM targets not distinguished")
    return {"eta": 2., "random_variance": 1., "at_random_effect_zero": at_zero,
            "integrated_logit_normal_mean": marginal}
check("derived_logit_zero_RE_differs_from_integrated_mean", nonlinear_mean)


def symmetry():
    value = float(np.dot(w, logistic(np.sqrt(2.) * u)))
    require(np.isclose(value, .5), "Logit-normal symmetry failed")
    return {"integrated_mean_at_eta_zero": value}
check("derived_logit_normal_symmetry", symmetry)


def poisson_marginal():
    eta, variance = .7, 1.2
    num = float(np.dot(w, np.exp(eta + math.sqrt(variance)*u)))
    exact = math.exp(eta + variance/2)
    require(np.isclose(num, exact), "Lognormal moment identity failed")
    return {"numerical": num, "closed_form": exact}
check("derived_log_link_marginal_mean", poisson_marginal)


def mc_precision():
    s1 = math.sqrt(.05*.95/1000)
    s2 = math.sqrt(.05*.95/10000)
    require(abs(s1-.0069) < .00005 and abs(s2-.0022) < .00005, "MC examples wrong")
    return {"B_1000": s1, "B_10000": s2}
check("derived_monte_carlo_standard_error_examples", mc_precision)

result = {
    "verification_date": datetime.now(timezone.utc).date().isoformat(),
    "checks": checks,
    "static_and_algebra_checks_passed": sum(c["status"] == "PASS" for c in checks),
    "static_and_algebra_checks_failed": sum(c["status"] == "FAIL" for c in checks),
    "Rscript_found_in_this_execution": shutil.which("Rscript"),
    "R_runtime_tests": "NOT EXECUTED by this validator",
    "agent_behavior_evaluations": "NOT EXECUTED",
    "independent_statistical_review": "NOT PERFORMED",
}
if args.output:
    args.output.write_text(json.dumps(result, indent=2)+"\n")
print(json.dumps(result, indent=2))
raise SystemExit(1 if result["static_and_algebra_checks_failed"] else 0)
