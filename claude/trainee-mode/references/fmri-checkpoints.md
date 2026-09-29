# fMRI learning checkpoints

Use only the examples matching the learner's selected goals. These are prompts,
not analysis recipes or scientific acceptance thresholds. Reuse the active fMRI
workflow's approved plan, teaching review style, and data-disclosure boundary.

| Goal | Initial question | Graduated support | Evidence for feedback |
|---|---|---|---|
| Choose or explain a contrast | Which condition difference answers this question, and what would a positive estimate mean? | Hint: identify the coefficient names and ordering. Example: work through a different two-condition contrast. Then explain the current contrast if needed. | Actual design columns, contrast weights, estimability, and the scientific estimand. |
| Read motion QC | What pattern concerns you, and what would you check before deciding what to do? | Hint: orient to units, time axis, and event timing. Example: show a synthetic transient versus sustained pattern. Then give the full assessment. | Motion/confound series, acquisition timing, temporal coverage, protocol criteria, and consequences for available data and design. |
| Read registration QC | Where does alignment look plausible or questionable, and what additional view would help? | Hint: identify which images and spaces are overlaid. Example: inspect boundaries in another plane. Then give the full assessment. | Source/target identity, spatial metadata, overlays across multiple slices/planes, and the relevant downstream analysis. |

Deliver one support level at a time, waiting for the learner to respond. Do not
show the entire table or answer sequence as a substitute for interaction.
Use accessible images or descriptions when the learner cannot open the report.

A concerning motion plot does not itself establish an exclusion rule. A smooth
registration image does not itself establish anatomical correctness. Ground
feedback in the actual artifacts and protocol; unresolved cases stay unresolved.
Do not adjust thresholds or contrasts to confirm a prediction.

Possible hands-on steps include writing a contrast vector and checking its
meaning against the design, or opening an approved QC overlay and describing
the evidence. Identify who actually executes any code, inspect the output
together, and distinguish an independent explanation from a prompted one.
