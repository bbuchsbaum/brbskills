## Can this Apple Silicon workstation run the pinned fMRIPrep image?

**Not yet established.** None of the evidence so far shows that it can or that it can't. We know the host architecture, but not the image's supported platforms or the runtime route, so neither "native", "emulated" nor "incompatible" is a supported claim yet.

### What we know (as you reported it)
- **Host:** Apple Silicon, so arm64 (aarch64) CPUs running macOS.
- **Image:** pinned. I don't have its exact reference or digest yet.
- **Linux containers need a Linux VM on macOS.** Docker Desktop, Colima, OrbStack, Podman and Apptainer-in-a-VM all run one. So the architecture that matters is the VM's, not macOS's, and the VM's CPU and memory limits are the real resource budget.

### What we don't know yet (blocks a yes or no)
| Question | Why it matters | How to settle it |
|---|---|---|
| The exact image reference and digest | Architecture is a property of that specific manifest, not of a tag name or release number | You supply it |
| Which platforms that manifest lists (linux/arm64, linux/amd64, or both) | Decides between native and emulated execution | `docker buildx imagetools inspect <image>@<digest>` (or `docker manifest inspect`). For a local copy: `docker image inspect --format '{{.Os}}/{{.Architecture}}' <image>@<digest>` |
| Which runtime you'd use and its server architecture | The runtime decides whether an amd64-only image can run at all | `docker version` (Server OS/Arch) and `docker info`, or the equivalent for your runtime |
| Whether amd64 emulation (Rosetta or QEMU) is enabled in that VM | Without it, an amd64-only image will fail with an exec-format or platform-mismatch error | Runtime settings, then a real run (below) |
| VM CPU and memory allocation, and file-sharing mounts | Sets `--nprocs`, `--omp-nthreads` and `--mem-mb`, and decides whether BIDS, output, work, license and TemplateFlow paths are visible | `docker info` (CPUs, Total Memory) and a mount probe |

### What would not count as proof
- A tag like `25.2.x`, a file name, or a local `.sif` name. None of these state the architecture.
- `docker pull` succeeding. Without `--platform`, the pull just picks a variant, and it may pick the wrong one silently.
- `fmriprep --version` succeeding. It shows that the entrypoint starts. It says nothing about asset completeness, mounts, performance, or whether the heavy tools (FreeSurfer, ANTs, AFNI, FSL) behave correctly under emulation.

### Smallest next step
1. Send me the pinned reference with its digest and tell me which runtime you plan to use (Docker Desktop, OrbStack, Colima, Podman, or something else).
2. Run the manifest inspection above. That settles the first question from the registry without executing anything.
3. If the image is amd64-only and emulation is on, the next proof is a short in-runtime probe with the platform set explicitly (for example, `--platform linux/amd64 ... --version`, plus `uname -m` via `--entrypoint`). That would show the emulated path starts. Readiness for real work still needs a one-participant pilot through the same runtime, mounts and resource limits, with its outputs and QC reviewed. Expect emulated runs to be substantially slower than native. I can't promise any particular runtime until the pilot has been measured.

If the manifest has no arm64 variant and your runtime can't emulate amd64, this workstation can't run the pinned image as-is. Switching to a different image or version to make it fit would change the recipe, so it would need your explicit approval. The alternative is to run the same pinned image on an x86_64 host or cluster.

**Two questions:**
1. What is the exact pinned image reference, with its digest?
2. Which container runtime would you use on this Mac, and is amd64/Rosetta emulation enabled in it?
