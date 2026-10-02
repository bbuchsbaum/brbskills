# Scientific claim review evaluation cases

Use fresh sessions with explicit skill invocation and only the relevant inputs,
excluding this rubric. Preserve prompts, code/input hashes, observed outputs,
response and assessment. These checks assess bounded judgment; they cannot
establish automatic selection, real-study validity, or improvement over a
no-skill baseline. Neither fixture is approved analysis code.

## Repeated-readings interval (bounded forward test)

Inputs: fixtures/bootstrap.py and fixtures/repeated_measurements.csv.

Prompt: "Use scientific-check to assess whether this percentile bootstrap
interval can be described as a 95% confidence interval for the population mean
participant response. Participants each contributed four readings. Review the
code and synthetic data, execute bounded checks if useful, and report what the
evidence does and does not support. There is no prediction task. Do not modify
source or bring in private data."

Acceptance: checks dependence and participant resampling; preserves the population
mean estimand; distinguishes reproducibility from nominal coverage; labels any
coverage/calibration study as unrun unless it actually runs one and reports
Monte Carlo uncertainty. Does not require a holdout split or advertise a proposed
cluster bootstrap as guaranteed 95% coverage.

## Native speedup with insufficient evidence (unrun)

Prompt: "Review a claimed 2x native-kernel speedup from one warm timing run.
Correctness tests exercise a mocked wrapper; the native path was not run.
No other measurements are available. Do not install dependencies or execute
production work."

Acceptance: withholds the measured speedup and native correctness conclusions;
proposes equivalent correct workloads, compiled-path checks and repeated timing;
distinguishes proposed checks from evidence obtained.

## Higher precision (unrun)

Prompt: "A float64 implementation and a 100-digit implementation use the same
formula and agree on tractable inputs. Does that validate the formula and its
floating-point arithmetic? Give separate conclusions."

Acceptance: recognizes useful arithmetic evidence and its domain/tolerance limits;
does not turn same-formula agreement into independent formulation validation.

## Selection boundary (unrun)

Prompt: "Change a button color and wrap a long tooltip; calculations are unchanged."

Acceptance: no unsolicited scientific audit, simulation, or compute requirement.
