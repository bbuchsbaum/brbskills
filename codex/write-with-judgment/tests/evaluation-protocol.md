# Evaluate editorial judgment

Use this protocol when developing or assessing the skill. It is not part of the writing workflow. Keep evaluation prompts separate from expected outcomes during generation.

## Build a varied set of tasks

Use original or authorized passages. Include weak writing that needs decisive repair and good writing that needs little intervention. Cover these cases:

| Task family | Check the result for… |
| --- | --- |
| Manuscript section with a buried governing claim | Structural repair under a rewrite brief; a report, not a rewrite, under a light-edit brief. |
| Scientific result with a null finding and a qualified interpretation | Preserved uncertainty, test scope, population, and causal limits. |
| Results reported at more than one level or for more than one group | Each result and qualifier stays attached to its own level or group. |
| Software documentation with guarantees, defaults, and failure cases | Guarantees not inflated; costs and failures kept visible. |
| Procedure with permission, recommendation, prerequisites, and exceptions | Preserved modal force, branching, sequence, and thresholds. |
| Numbers that remain unchanged while group labels move | Correct roles and relationships despite identical literal inventories. |
| Citation supporting only one clause | Preserved claim-to-source attachment. |
| Non-default English variety under a venue's explicit style | Correct precedence of user instructions, venue choices, and locale. |
| Strong technical or methods prose with legitimate passives and technical nouns | Restraint and precision. |
| Literary prose with repetition, a fragment, or delayed revelation | Preserved voice, implication, and timing. |
| Conflicting evidence under a strict summary limit | Necessary omissions without false consensus or dropped limitations. |
| Elegant prose containing a broken argument | Substantive repair when authorized, without invented evidence. |
| Fresh draft from a sparse factual brief | Useful composition without fabricated detail. |
| Simple spelling or punctuation correction | A prompt, proportionate result without excessive ceremony. |

Also include false friends: “robust regression,” different operations called “verify” and “validate,” negation whose deletion changes the result, and direct quotations that depart from house style. Avoid relying only on examples already in the package.

## Compare fairly

Run the same prompts with and without the skill when assessing improvement over ordinary prompting. Keep model, material, instructions, and available evidence matched. Randomize candidate order for reviewers. Supply the source and brief; withhold the editing rationale and condition labels.

Evaluate at the level of the requested task:

1. Check factual support, required meaning, citation attachment, and explicit constraints. A material defect cannot be redeemed by fluent wording.
2. Judge organization, interpretability, economy, and effect in context.
3. Judge whether intervention matched the requested depth and preserved effective voice.
4. Record unnecessary questions, tool work, and explanation that delayed an otherwise simple result.

Use pairwise preferences or dimension-specific judgments with short evidence-based reasons. Permit ties and a preference for the unedited source. Do not combine everything into an opaque quality score. Report individual failure types, not just a win rate.

## Check the utility independently

Run the bundled regression checks from the skill directory:

```bash
python3 -B tests/test_compare_anchors.py
```

Run actual command-line fixtures for changed numbers, units, comparators, code, URLs, locked terms, repeated occurrences, and modality. Include harmless line wrapping and unchanged domain terminology. Verify error handling for missing files. Include a changed-relationship example with identical inventories; its output must explicitly decline a semantic verdict.

Treat small forward tests as development checks. Do not claim benchmark superiority, cross-model reliability, or deterministic semantic equivalence from them. Preserve concrete failures, update the narrow instruction that caused them, and test fresh passages before attributing an improvement to the change.
