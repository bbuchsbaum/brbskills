# Worked editorial decisions

Use these original, hypothetical examples to calibrate judgment. The preferred wording is one defensible result, not a mandatory answer. Read the task before choosing the permitted edit.

Contents: scientific precision · permission and recommendation · necessary conditions · text an agent must parse · useful passive voice · terminology · literary non-edit · deliberate repetition · substantive repair · summary · claim needing evidence.

## Scientific precision

**Request:** Tighten this finding for a scientific reader.

**Source:** It is worth noting that although unemployment was associated with property crime across counties, the association was not statistically significant across states.

**Revision:** Unemployment was associated with property crime across counties; the state-level association was not statistically significant.

**Decision:** Remove the introductory filler and make the comparison visible. Preserve the two levels of analysis and the limited null statement. A revision asserting that the variables were unrelated at the state level would make a stronger claim.

## Permission and recommendation

**Request:** Make the instruction easier to follow.

**Source:** Reviewers may release the files only if all authors have approved them, and reviewers should keep a copy for 30 days unless the project requires a longer retention period.

**Revision:** Reviewers may release the files only after all authors approve them. Reviewers should retain a copy for 30 days, or longer if the project requires it.

**Decision:** Separate release from retention. Preserve permission, unanimous approval, a recommendation rather than a new requirement, and the longer-retention exception. Do not add a new approval mechanism or deletion policy.

## Necessary conditions

**Request:** Check this simplification.

**Source:** The service may retry only if the operation is idempotent.

**Candidate:** If the operation is idempotent, retry it.

**Decision:** Reject the candidate. The source restricts when a retry is permitted; the candidate orders a retry whenever the condition holds. A service could satisfy the source by choosing not to retry. Keep the source, or write: “A retry is permitted only for an idempotent operation.”

## Text an agent must parse

**Request:** Make this tool description unambiguous for an agent.

**Source:** Spins up a sandbox and runs the user's script; files not saved to /out are discarded when the session has ended, and network access may be restricted depending on workspace policy.

**Revision:** Starts a sandbox and runs the supplied script in it. When the session ends, the sandbox deletes every file outside `/out`. Network access may be restricted by the workspace policy.

**Decision:** Replace the idiom, split the three facts, and resolve the ellipsis ("files not saved to /out") into an explicit scope. Keep "may be restricted": the source does not say access is always restricted, so the hedge is content. Do not add a list of blocked hosts or a retention period the source never gave. A mechanical rewrite that capped every sentence and banned the hedge would have produced "Network access is restricted", which is a different claim.

## Useful passive voice

**Request:** Lightly polish this methods sentence.

**Source:** Samples were incubated at 37 °C for 24 h.

**Revision:** Samples were incubated at 37 °C for 24 h.

**Decision:** Leave a clear sentence alone. Adding an unspecified researcher or instrument to force an active construction would create content. Add acquisition details only when the task and evidence supply them.

## Terminology that earns its place

**Request:** Check this technical prose for unnecessary jargon.

**Source:** We used robust regression to reduce the influence of extreme observations. We verified the checksum before validating the model.

**Decision:** Preserve “robust regression” as a method name and the distinction between checksum verification and model validation. Explain the method further only if the audience needs it. Do not treat co-occurring near-synonyms as evidence that the concepts are identical.

## A literary non-edit

**Request:** Light polish; keep the understated tone.

**Source:** He kept the receipt long after he had forgotten what he bought.

**Revision:** He kept the receipt long after he had forgotten what he bought.

**Decision:** The sentence is clear, economical, and suggestive. Explaining the implied attachment or replacing the past perfect merely to simplify the tense would reduce its effect.

## Deliberate repetition

**Request:** Tighten without losing the joke.

**Source:** The committee waited for the report. The report waited for the data. The data, being data, had no opinion on the matter.

**Revision:** The committee waited for the report. The report waited for the data. The data, being data, had no opinion on the matter.

**Decision:** The repeated construction carries the joke. Replacing it with one efficient sentence would remove the timing. If a surrounding paragraph repeats the same joke, edit that context instead.

## A substantive repair

**Request:** Improve the argument using only these stated results.

**Source:** Average throughput rose after the new scheduler was deployed. Therefore every team benefited, and the scheduler caused the gain. There was no comparison cluster, and per-team changes were not analysed.

**Revision:** Average throughput rose after the new scheduler was deployed. Without a comparison cluster, the gain cannot be attributed to the scheduler alone. Because per-team changes were not analysed, the average does not establish that every team benefited.

**Decision:** The task authorizes argument repair. Identify the two changed conclusions in a brief note: the aggregate result does not establish universal benefit, and the design does not isolate the proposed cause. Do not invent a comparison or per-team data.

## A summary can omit without distorting

**Request:** Summarize the result in one sentence, retaining the main limitation.

**Source:** A pilot included 18 volunteers. Twelve preferred the new interface. Five preferred the old interface, and one expressed no preference. Recruitment was by convenience. The team will conduct a larger comparison next quarter.

**Revision:** In a convenience sample, 12 of 18 volunteers preferred the new interface; the sampling method limits how broadly the result can be generalized.

**Decision:** Preserve the central comparison and limitation. The purpose allows omission of the other counts and future plan. Do not say all users preferred the interface or that a representative sample was tested.

## A claim needing evidence

**Request:** Make this description more concrete without inventing facts.

**Source:** Our software delivers unparalleled reliability.

**Decision:** A meaningful concrete replacement needs evidence such as observed availability, a comparison, or documented failure behaviour. Identify that gap and draft from any supplied evidence. Do not replace the boast with an invented uptime percentage. If only copyediting is requested, retain the claim as the author's claim and flag its unsupported comparison.
