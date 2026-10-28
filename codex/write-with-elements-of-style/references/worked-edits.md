# Worked editorial decisions

These are original teaching examples, not quotations from Strunk, White, or Orwell. Use them to transfer the principles, not as sentence templates. Each change requires a reader-facing reason.

## Contents

1. Recover the action
2. Keep evidential uncertainty
3. Choose voice from agency and topic
4. Preserve a condition's scope
5. Repair paragraph order
6. Make ideas parallel
7. Keep terminology stable
8. Ground concrete detail
9. Preserve rhythm
10. Preserve the author's position
11. Keep useful negation
12. Leave effective prose alone
13. State the relationship directly
14. Remove manufactured importance
15. Resolve an instruction before shortening it
16. Account for a substantive cut

## 1. Recover the action

**Before:** The committee undertook an examination of the proposal and arrived at the conclusion that a revision was necessary.

**After:** The committee examined the proposal and concluded that it needed revision.

**Why:** Informative verbs replace nominal scaffolding without inventing a decision or strengthening its force. Do not shorten this to “The committee rejected the proposal”: rejection is a different action.

## 2. Keep evidential uncertainty

**Before:** It is possible that the observed difference may reflect variation in attention, although the study does not establish this explanation.

**After:** The observed difference may reflect variation in attention, but the study does not establish this explanation.

**Why:** Remove duplicate uncertainty; retain the substantive qualification. “Variation in attention explains the difference” would be a factual change, not an improvement in style.

## 3. Choose voice from agency and topic

**Before:** The reviewers evaluated each submission. A decision was then communicated by the editor to the authors.

**After:** The reviewers evaluated each submission. The editor then communicated a decision to the authors.

**Keep:** Each vial was labelled before storage.

**Why:** The first passage supplies an actor whose action is buried. The vial sentence can properly keep the object and sequence in focus when the labeller is immaterial or unspecified. Do not insert “we” just to force active voice.

## 4. Preserve a condition's scope

**Before:** Access is granted only after approval, except that emergency access may be granted before approval if the duty officer authorizes it.

**After:** Access requires approval. The duty officer may authorize emergency access before approval.

**Why:** The actor, discretion, exception, and sequence survive. “The duty officer authorizes emergency access” would convert permission into a reported or required action.

## 5. Repair paragraph order

**Before:** We will need a decision by Friday. The archive is growing quickly. The old server has no room for another backup. We can expand the server or move the archive. Moving it would interrupt access for a day.

**After:** The archive is growing quickly, and the old server has no room for another backup. We can expand the server or move the archive; moving it would interrupt access for a day. We need a decision by Friday.

**Why:** The problem leads to the options, their consequence, and the deadline. A procedural memo might instead lead with the deadline. The useful relationship determines the order.

## 6. Make ideas parallel

**Before:** The tool helps users inspect a file, checking its metadata, and they can export a report.

**After:** The tool helps users inspect a file, check its metadata, and export a report.

**Why:** The three capabilities belong at the same grammatical level. Do not make a limitation or a cause parallel to a capability merely to create a neat list.

## 7. Keep terminology stable

**Before:** The model estimates working-memory capacity. This mental capability is then used to predict recall, and the cognitive resource is compared across groups.

**After:** The model estimates working-memory capacity, which is then used to predict recall and compared across groups.

**Why:** The same construct has one name. Verify whether the estimates or the construct are the actual predictor; if the distinction matters, write “The estimated capacity…” rather than hiding it. Repetition can be more accurate than decorative synonyms.

## 8. Ground concrete detail

**Before:** The programme had a major impact on the community.

**If the brief supplies the facts:** The programme provided evening transport for 80 residents.

**If it does not:** Flag that “major impact” needs a specific result; retain a qualified statement or an explicit placeholder as the task permits.

**Why:** A precise invented number is worse than a vague supported claim. The concrete version is a possible replacement only with the stated evidence.

## 9. Preserve rhythm

**Original:** She waited through the rain, through the last bus, through the hour when the shops went dark.

**Decision:** Keep it if the passage needs its accumulating rhythm.

**Why:** “She waited a long time” is shorter but discards the imagery, progression, and emotional duration. Repeated structure can create the effect the writer wants.

## 10. Preserve the author's position

**Before:** The policy is unfair because it charges applicants who cannot choose another provider.

**Light edit:** The policy is unfair: it charges applicants who cannot choose another provider.

**Unjustified rewrite:** The policy raises questions of fairness, although providers must also cover their costs.

**Why:** The last version weakens the stated judgment and adds an unsupplied counterargument. A substantive critique may examine that position; a copyedit may not silently replace it.

## 11. Keep useful negation

**Original:** We found no evidence that the intervention improved retention.

**Decision:** Retain the evidential scope.

**Wrong:** The intervention did not improve retention.

**Why:** Failure to find evidence is not proof of no effect. The instruction to write positively cannot license a different scientific conclusion.

## 12. Leave effective prose alone

**Original:** The door opened. Nobody came in.

**Decision:** Keep both sentences if that is the intended narrative beat.

**Why:** Combining them, adding an adverb, or explaining the suspense need not improve anything. A passage earns its form by what it does for the reader, not by how many rules an edit can visibly apply.

## 13. State the relationship directly

**Before:** Setting either matrix to something other than the identity is how you tell the decomposition to use a different metric.

**After:** A nonidentity matrix specifies a different metric for the decomposition.

**Why:** The original proposition becomes the sentence's main assertion. Retain the surrounding definitions of the two matrices and their respective metrics; this sentence cannot replace them.

## 14. Remove manufactured importance

**Before:** It is worth understanding the crucial distinction here: the cache stores parsed files, not query results. This is not merely an implementation detail; it fundamentally shapes how you should think about reuse. The honest answer is that a new query still runs.

**After:** The cache stores parsed files. Each new query runs against those files; its results are not cached.

**Why:** The revision gives the reader the mechanism and consequence without staging a revelation. Its rhythm follows the explanation. Contrast is useful here, but repeating and announcing it adds no information. This example diagnoses the passage's effect, not its authorship.

## 15. Resolve an instruction before shortening it

**Before:** To disable the penalty, drop `lambda_v`.

**If the documented API says omission restores the default and zero disables it:** To disable the penalty, set `lambda_v = 0`. Omitting `lambda_v` restores the default penalty.

**If the API is unknown:** Flag whether “drop” means omit the argument or set it to zero. Do not choose either operation without support.

**Why:** A short, grammatical instruction can produce the wrong call. Resolve the operation before polishing the sentence; keep any unresolved factual question visible.

## 16. Account for a substantive cut

**Original:** Earlier versions processed one file at a time. The current version batches files, reducing setup work but requiring more memory. Use single-file mode when memory is limited.

**Unjustified cut:** The current version batches files to reduce setup work.

**Decision:** Keep the memory tradeoff and single-file advice. Retain the historical comparison in migration guidance; in a current-use quickstart, it may be removed or relocated.

**Why:** The cut removes both a cost and an actionable alternative. Account for what disappears and judge it against the reader's purpose. Shortening alone does not justify the loss.
