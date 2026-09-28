# Trace

Files read:
- /Users/bbuchsbaum/code/brbskills/skills/fmriprep/SKILL.md
- references/operations.md (full)
- references/semantics.md (sections: version drift, anatomy/FreeSurfer, precomputed derivatives) via sed
- references/execution.md (probe list item 6 on output-dir version warning; work-dir reuse paragraph) via sed/grep
- references/sources.md (grep for S13)

Commands run:
- cat/sed/grep on the above skill files; ls of the working dir
- Wrote response.md and trace.md in the working dir

Not run: fake_runtime.py, fake_scheduler.py (no execution step warranted; request declined as incompatible reuse).
