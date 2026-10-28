# Editorial evaluation cases

These are manual behavioral cases, not executed tests. For development, give a fresh session the skill and one prompt below, withholding the assessment criteria. Record product/model, prompt, files read, output, and reasons for each verdict. Use matched previous-version or no-skill runs before claiming improvement. Assess fidelity and writing quality separately; passing packaging checks proves neither.

## Comprehensive coverage

**Prompt:** Review this entire guide for meaning and style, then revise it. Account for all reader-facing elements.

> # Cached searches
>
> It is worth understanding that caching is an important capability.
>
> ## Operation
>
> The cache stores parsed files. Queries still execute.
>
> | Setting | Meaning |
> | --- | --- |
> | `cache = false` | Reuse parsed files. |
>
> Figure caption: Disabling the cache reuses previously parsed files.
>
> ## Limits
>
> The API reference says `cache = false` disables reuse. Cached files remain in memory until the session ends.

**Assess:** Covers headings, body, table, caption, and relationships between them. Catches the table and caption contradictions, retains the memory limit, improves the empty opening, and reconciles findings with actual edits. Does not invent an API beyond the supplied reference statement or manufacture findings for sound elements.

## Technical ambiguity and directness

**Prompt:** Improve this documentation. The API default is `alpha = 1`; zero disables the penalty.

> To disable the penalty, drop alpha. Setting the weight to something other than one is how you tell the solver to use a different scale.

**Assess:** Specifies `alpha = 0`, preserves the default, and directly states the weight/scale relationship. Does not prioritize cosmetic edits over the misleading operation. Repeat without the API sentence: the operation should remain an explicit factual question.

## Voice with restraint

**Prompt:** Improve the explanation and lightly edit the narrative. Preserve useful character.

> Explanation: The honest answer is that retries take time. This is not just a detail; it is a crucial distinction. Each retry waits two seconds. That is the key takeaway.
>
> Narrative: He checked the latch, checked the window, checked the empty street. Nothing moved.

**Assess:** Makes the retry delay direct and removes redundant importance claims. Preserves the narrative's purposeful repetition and pause. Does not mechanically ban contrasts, triads, or repeated words, diagnose AI authorship, or add a closing maxim. Judge cadence and specificity as well as factual fidelity.

## Cuts and reconciliation

**Prompt:** Shorten this migration note without losing operational guidance. Explain substantive cuts.

> Version 1 loaded each image separately. Version 2 batches images to save setup time. Batches use more memory. If a batch exceeds available memory, select single-image mode. Version 1 required a separate setup step for each image.

**Assess:** Removes redundant history while retaining the version distinction needed for migration, the memory cost, and the fallback condition. Explains any substantive loss or relocation. Final wording supports the same actions and conditions; a faithful but clumsy rewrite still needs craft work.
