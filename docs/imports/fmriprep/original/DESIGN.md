# Design: scientific plan, verified execution, durable evidence

## Recommendation

Build one self-contained fmriprep skill with a short entrypoint and selectively
loaded references. Make the repository launcher an adapter, not the definition of
fMRIPrep. Give the execution boundary a small documented contract that can be
satisfied by an Alliance skill, a lab-specific profile, or the fmriprep agent itself.

This is dependency inversion at the instruction/artifact level. The skill says
what must be true for the approved recipe to execute; it does not require a
particular brand of cluster, container runtime, or companion skill.

## Why this boundary fits the repository

The reviewed repository already separates configuration/runtime helpers,
command construction/Slurm rendering, and interactive frontends. It already has
INI layering, subject batching, concurrency controls, manifests, and rerun support.
Preserve those facilities. The companion contributes missing scientific inference,
brief decision handling, version-aware knowledge, and stronger environment proof.
See the pinned adapter reference for exact source findings.

Do not make the agent drive the GUI or wizard when noninteractive interfaces
exist. Do not put every site policy in the scientific skill. Do not duplicate the
launcher in another several-thousand-line Python implementation.

## The execution contract

`plan.json` describes what preprocessing means for this dataset. `execution.json`
describes how an identified installation can perform it on an authorized target.
`receipt.json` records what was actually submitted and observed. These files are
small data structures and documentation, not a new public API already implemented
by the repository.

A scientific hash includes data selection, input identity, methods, outputs, and
software identity. The execution hash identifies site setup, resources, path
mapping, scripts, staged assets, and other execution settings. The receipt records
both, so an allowed memory/concurrency adjustment does not masquerade as the same
execution, and an SDC/template/version change cannot masquerade as a harmless
infrastructure repair. Thread/seed/runtime choices remain in provenance even
when they are treated as execution rather than scientific settings.

The provider may change partition, module setup, runtime mount details, resource
translation, or staging arrangements within authorization. It cannot remove
FreeSurfer, change output templates, force a different SDC method, exclude runs,
upgrade fMRIPrep, or drop requested outputs to fit its preferred launcher.

A site skill should resolve and verify first, then return evidence and a renderable
execution record. The orchestrating fmriprep agent owns submission unless explicitly
delegated. This avoids two skills launching the same job while each assumes the
other is only advising.

## Environment discovery is not environment proof

The skill keeps provisioning, runtime, scheduling, and storage as separate axes.
Modules can expose native executables or container wrappers. A Docker executable
may not have daemon access. The login node may see different mounts and internet
access from a compute node. An x86 image on another architecture may require a
different route. None is solved by a hostname lookup table alone.

The workflow is candidate profile -> host observations -> actual compute-context
probe -> representative full-quality pilot -> qualified profile for that scope.
Only the last steps establish execution readiness. Cache profiles by identity and
revalidate drift; do not ask the user the same site questions every session.

The probe is cheap relative to an fMRIPrep cohort, but its resource request and
submission still require authorization. It checks actual image execution, binds,
writable output/work/status/HOME/tmp, version and CLI, allocation visibility, and
assets. Offline completeness includes implicit templates and model resources,
not merely the chosen MNI output template. A completed pilot remains necessary
because `--version` does not traverse the workflow's dependency graph.

## Adaptive decisions

The BIDS inventory precedes the interview. Resolve inheritance and per-run fieldmap
coverage using mature tooling; do not invent a second incomplete BIDS implementation
inside a convenience script. Collapse observations into common cases and exceptions.

In brief mode, present one recipe and ask for changes. Budget at most three material
questions in the initial round. The budget limits unnecessary interrogation, not
safety: essential missing information still blocks affected jobs. Every setting
carries a source: observed data, explicit request, locked project policy, confirmed
conditional preference, or proposed default.

The persistent stores serve different purposes. User preferences say, for example,
which template to propose for a scoped type of study. Site profiles say which
module and filesystem contract worked on an identified target. Run receipts say
what actually happened. Do not blur these or silently turn a one-off correction
into a universal default.

## Compression with semantic checks

The entrypoint contains routing, workflow order, invariants, and deliverables.
References encode decisions as conditions and consequences, not a comprehensive
CLI dictionary. Mutable flag syntax is verified from the chosen executable and
versioned documentation. Routine shell/Python knowledge can remain with the model.

High-value information to retain includes distinctions easily lost in a terse
prompt: template identity versus grid; native anatomical versus native BOLD versus
native surface; acquired fieldmap availability versus per-run applicability;
surface-output choice versus reconstruction effects; confound generation versus
denoising; input validation versus indexing; compute success versus QC; and
local process visibility versus durable scheduler ownership.

Instruction-only operation is valid on an unfamiliar system. Deterministic helpers
should be added only where they eliminate repetitive parsing/validation or known
failure modes. The initial helper inventories the host without pretending it
understands BIDS or qualifies the installation.

## Focused engineering sequence

**First useful version:** install this skill; exercise it with a valid small dataset
and the existing verified Apptainer/Slurm route; resolve explicit output/reconstruction
settings; preserve the exact command and pilot evidence. Then test the same recipe
without rriscripts. The scientific plan and output requirements should match.

**Launcher hardening:** fix explicit image selection for fmriprep-docker; preserve
argv across direct and batched execution; expose effective config/capabilities;
add structured file mounts and general module setup; return submission/attempt
identities and separate process success from verified output status. Keep one
payload implementation across local and scheduler modes.

**Portable qualification:** add a direct Docker route, a native/module route, and
one non-Slurm scheduler fixture. Establish host-versus-compute path tests, offline
asset tests, allocation limits, restart ownership, and lost-acknowledgement handling.
Reuse a general site-profile schema only after these independent use cases confirm
its value. Do not build a fleet scheduler as a prerequisite to preprocessing.

## Acceptance criteria

Require preserved scientific intent across wrapper/direct/provider routes, zero
fabricated metadata or site accounts, explicit software identity, minimal questions,
no full-cohort launch before the approved pilot gate, and an auditable output/QC
handoff. Test mutations, not only happy paths: module exists but image is absent;
login-only writable path; missing inherited SliceTiming; broken fieldmap links;
mutable image tag; quoted filter path; stale cache; duplicate live subject job.

Measure task success, unsafe actions, unnecessary questions, tokens consumed,
wrong reference loads, and recovery quality. Compare the base model alone, the
compact skill, and the skill plus launcher. Compress only when held-out reliability
is preserved. The goal is successful verified preprocessing per unit of context,
not the shortest SKILL.md regardless of omitted conditions.

## Delivery status

This is an authored skill and architecture proposal with a locally tested host
probe. It is not a claim of a validated universal execution engine. Repository and
official documentation were inspected; no fMRIPrep dataset, Docker/Apptainer image,
or real scheduler job was executed in this authoring session.
