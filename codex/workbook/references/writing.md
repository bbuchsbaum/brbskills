# Writing a workbook entry

An entry is read by someone switching in from other work. They read the
question and the answer and perhaps nothing else, so those two must carry the
result by themselves. The sections below them exist so a careful reader can
check the answer.

Write plainly, in full sentences. Prefer the concrete word to the abstract
one and the short sentence to the long one. Use a technical term when it is
more exact, and define project shorthand on first use or link the glossary.

## Title

A noun phrase of at most 40 characters that distinguishes this entry from its
neighbours in the sidebar: "WM transfer with 4 mm betas", "Vowel IC by
parcel", "cvMANOVA localizer screen". Put variants that matter (smoothing,
atlas, window) in the title, because superseded and current versions will sit
side by side.

## Question

One sentence that a reader could answer yes, no, or with a number. Avoid
method names unless the question is about the method.

- Weak: "GPCA transfer analysis."
- Better: "Does the vowel geometry learned during listening predict which vowel is held in working memory?"

## Answer

At most 70 words, in this order:

1. The direct answer.
2. The key estimate with its uncertainty and the test: "accuracy 0.53 (95% CI 0.51–0.56; permutation p = .004, Holm across 6 regions)".
3. The one qualification that matters most.

For a null result, say what effect size could have been detected, if that is
known. Do not round away the uncertainty. Do not write "significant" without
the test.

## Approach (brief methods)

At most about 200 words. A reader should be able to tell what was compared
with what, and whether the inference is sound. Cover, in order:

- **Data.** Which inputs (for example, which trial betas and smoothing), how many participants, runs and trials. Counts, never identities.
- **Model.** The statistic or classifier and its key settings.
- **Validation.** The cross-validation scheme and what was held out, with the unit of independence.
- **Inference.** The test, its null distribution and how it was generated, and the level at which it was applied (participant, group).
- **Multiplicity.** What family was corrected and how.
- **Fixed or chosen.** Which choices were fixed before outcomes were seen, and which were made after looking. The latter make the entry exploratory.

Link the shared methods pages for anything standard (`{{< wbref trial-betas >}}`)
and state only what this analysis did differently. Full parameter lists, code
listings and derivations belong in the technical record.

## Results

Open with one sentence that states the result. Then show the evidence: at
most three figures or tables, each snapped from the analysis outputs.

- Every figure caption says what is plotted, the n, what the error bars or bands show, and where chance or the null lies.
- Every table has a caption and comes from a snapped TSV through `wbtable`.
- A number in the prose that is not in a table on the page is followed by an evidence link to the asset that holds it.
- Keep descriptive results and inferential tests visibly separate.

Use a tabset when the same result has parallel variants (task, window,
hemisphere), so the page stays short.

## Interpretation

What the result establishes, and what it does not. How it changes the
chapter's account. If it disagrees with an earlier entry, link that entry and
say which to believe and why. Distinguish "no evidence of an effect" from
"evidence of no effect"; only a sensitivity analysis or an equivalence test
licenses the second.

## Caveats

Specific limitations, not boilerplate:

- circularity (selection and test on the same data);
- choices made after looking at outcomes;
- assumptions that were not tested (exchangeability, stationarity);
- checks that were planned but not run;
- known defects in inputs or software.

## Log lines

One line per substantive change, dated: "2026-11-26 — Reran with 4 mm betas;
answer unchanged, intervals narrower." Say what changed and whether the
answer changed.

## Chapter and home syntheses

The chapter page's "Where this line of work stands" is two to five sentences:
the question the chapter pursues, what the current entries say together, and
what remains open, with a `wbref` link for each claim. The home page's "Where
things stand" does the same across chapters in at most about 300 words.
Rewrite these paragraphs; do not append to them.

## A worked example (synthetic)

```markdown
---
title: "Vowel decoding by region"
question: "Can vowel identity be decoded from auditory regions during listening?"
answer: "Yes in STG and PT (held-run accuracy 0.61 and 0.57 against chance 0.33; permutation p < .01, Holm across four regions). A1 and IFG did not exceed chance after correction, but their intervals overlap STG's, so the regional difference is not established."
kind: analysis
status: current
evidence: confirmatory
...
---

## Approach

Three-class vowel decoding on {{< wbref trial-betas >}} from 18 listeners,
six runs each. A ridge classifier per region, with the penalty tuned by
nested leave-one-run-out cross-validation and accuracy scored on the held
run. The group test compared mean accuracy with 1,000 label permutations
within run, applied identically to every participant. Holm correction
across the four regions fixed in {{< wbref regional-plan >}}.

## Results

Vowels were decodable in STG and PT but not, after correction, in A1 or IFG.

![Held-run vowel accuracy by region. Bars are group means across 18 listeners; whiskers are 95% bootstrap intervals over listeners; the dashed line is chance (1/3).](assets/<figure name>.png){#fig-accuracy}

{{< wbtable assets/<table name>.tsv cols="region,accuracy,ci_low,ci_high,p_holm" labels="Region,Accuracy,95% CI low,95% CI high,p (Holm)" digits=3 caption="Group accuracy by region." >}}
```
