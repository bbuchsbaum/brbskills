# write-with-elements-of-style import

Imported on 2026-10-27 from the user-supplied
`~/Downloads/write-with-elements-of-style.zip`. The
[original manifest](write-with-elements-of-style-original-manifest.json) records
the archive SHA-256 and the hashes of all 11 supplied files. Every source file
is preserved byte for byte in `skills/write-with-elements-of-style/`.

The package contains the operating guide, eight references, an SVG icon, and
Codex UI metadata. The references cover usage, composition, form, diction,
White's approach to style, Orwell, worked editorial decisions, and source notes.
The original source attachments and prior evaluation outputs are not included.

The repository builder generates `codex/write-with-elements-of-style/` and
`claude/write-with-elements-of-style/` from this shared source. Both include the
same guide, references, and icon, with a generated `SHA256SUMS`; only the Codex
bundle includes `agents/openai.yaml`. The imported metadata and invocation
policy are preserved. No scripts or runtime dependencies are required by the
writing skill. Global installation is separate from this repository import.

## Verification boundary

Checks completed on 2026-10-27 using the repository's `.venv`:

- `python scripts/skills.py sync` and `python scripts/skills.py check`: passed;
  both generated trees match their sources.
- `python -m unittest discover -s tests -v`: all 24 tests passed.
- The skill-creator `quick_validate.py` check: passed.
- `python scripts/skills.py package write-with-elements-of-style`: produced
  both product ZIPs. Each extracted bundle passed isolated validation, reference
  link checks, checksum verification, and exact comparison with builder output.
- All 11 imported files match the original manifest; all 1,215 pre-existing
  files inventoried under the source and generated trees remained unchanged.

Git's whitespace check flags a trailing space in the original diction heading
108 and a final blank line in the original style reference, repeated in both
generated bundles. These are retained to preserve the supplied files exactly.

These checks establish preservation and packaging integrity. They do not
recheck the digest against the original books or establish writing quality,
automatic selection, or successful execution inside Claude Code. The user's
creation summary reports nine paired writing tasks and an independent comparison
(seven ties, one skill preference, one baseline preference); the underlying
outputs are absent from this archive and were not independently verified during
import. No new model evaluation is claimed.

## Representative evaluation requests

The following cases are prospective checks, not reported passes:

- **Faithful copyedit:** "Lightly edit: We found no evidence that the intervention
  improved retention, although the sample was small." Preserve both the
  evidential scope and the qualification.
- **Reference selection:** "Use write-with-elements-of-style to explain whether
  imply or infer belongs in this sentence: These results infer that the method
  is robust." Consult the diction entry and distinguish usage from whether the
  evidence supports robustness.
- **Restraint:** "Review this sentence and change it only if the reader benefits:
  The samples were stored at 4 °C until analysis." Preserve the facts and accept
  passive voice when the actor is immaterial.
- **Outside the trigger:** "Compute the SHA-256 of this ZIP." Perform the file
  operation without invoking the prose-editing workflow.
