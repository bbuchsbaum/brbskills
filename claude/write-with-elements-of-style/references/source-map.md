# Sources, coverage, and editorial treatment

Consult this file when explaining a rule's provenance, checking the scope of the source digest, or distinguishing the original advice from this skill's adaptations. The operating guide and worked decisions are an original synthesis. The source references preserve the books' useful distinctions and exceptions without treating every historical preference as a current grammar rule.

## Primary material

1. William Strunk Jr. and E. B. White, *The Elements of Style*, fourth edition: the PDF supplied with the skill-creation request. Its 82 PDF pages include front matter, a scan note, and reflowed examples. This is the principal source.
2. George Orwell, *Politics and the English Language* (1946): the complete Markdown essay supplied with the request, including its five opening specimens, four diagnostic categories, principal examples, six rules, and qualifications. This supplies the smaller supplement.

Page numbers in the Strunk and White references are **1-based positions in the supplied PDF**, not page numbers in a printed edition. The package does not require access to either original attachment during normal use.

## Coverage

| Source material | Reference | Treatment |
| --- | --- | --- |
| Foreword and introduction, PDF pp. 5–10; afterword p. 75 | Composition | Reader's needs, revision, economy, rhetoric, and justified exceptions |
| Chapter I, PDF pp. 11–21 | Usage | All 11 numbered usage rules, their example families, and substantive exceptions |
| Chapter II, PDF pp. 22–35 | Composition | All 11 numbered principles, R12–R22, including paragraph and sentence-level craft |
| Chapter III, PDF pp. 36–39 | Form | All 11 headings, with historical production conventions distinguished from current requirements |
| Chapter IV, PDF pp. 40–60 | Diction | All 123 source entries, including compound headings, suffixes, and cross-reference entries |
| Chapter V, PDF pp. 62–74 | Style | All 21 reminders, introductory literary contrasts, explicit exceptions, and concluding attitudes |
| Glossary, PDF pp. 76–80 | Usage | Decision-relevant grammatical distinctions; redundant elementary definitions grouped |
| Orwell essay | Orwell | Central argument, diagnostic habits, lessons of the examples, all six rules, and limits |

The Strunk and White entries are condensed rather than merely selected. Repeated lexical instances of the same repair are grouped. Long literary extracts are summarized by the feature they demonstrate rather than transcribed. The digest does **not** claim to reproduce every original example sentence verbatim. It preserves the governing principle, distinctive example mechanisms, and relevant exceptions. Bibliographical/copyright pages and scan-production notes are not writing instructions.

## How to read the examples

Short source examples are retained or normalized; some are condensed or adapted. An arrow illustrates a possible repair, not a universal substitution. A chapter heading or source attribution does not make an adapted example an exact quotation. **Editorial adaptation** labels identify present-day application, qualification, or a safeguard added for an assistant. The worked-edits file contains original examples, not recovered source passages.

Several source pairs change specificity, causal force, certainty, or inferred intention. Rule 15 acknowledges guessing the intended Shakespeare criticism; other examples move from *can* to *will*, general weather to daily rain, *contact* to a phone call, or *facilities* to a toilet. Retain the technique; require evidence for the new details. Never treat these pairs as permission to fabricate.

Historical preferences about *hopefully*, generic *he*, singular *they*, restrictive *which*, *gotten*, *data*, *due to*, or productive suffixes require contextual judgment. Some are explicitly qualified elsewhere in the book. Preserve contemporary usage, people's pronouns, domain terminology, and the user's English variety. For an exact disputed requirement, consult the user's venue or a current authoritative reference rather than pretending this digest is a comprehensive current usage authority.

## Source defects

The scan note says original left/right examples are printed top/bottom. Local inconsistencies still occur. Obvious typographical corruption is normalized; uncertainty is retained where reconstruction would be unsafe.

- **PDF p. 32, Harrison example:** the rearranged relative clause can still appear to attach to the grandfather. Prefer an explicitly named subject or another sentence.
- **PDF p. 34, indirect-discourse tense and Friar example:** text is incomplete in the rendered PDF itself. The reference provides a conservative explanation and a clear illustrative sentence, not a purported verbatim recovery.
- **PDF p. 46, Fortuitous:** words are missing. The chance/fortune distinction is presented as a reconstruction.
- **PDF pp. 46–47, Get:** the prose's preference and the displayed example order conflict. Do not teach the display as an unambiguous before/after correction.
- **PDF p. 50, Line:** the French-literature example is garbled. The reference labels the normalized reconstruction.

## Skill design references

The portable structure uses `SKILL.md` with name/description metadata and direct links to references. Its concise core and selective loading follow [Anthropic's skill-authoring guidance](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices). Its metadata also fits [Claude's custom-skill guidance](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills). These documents concern packaging and workflow; they do not establish the writing quality of this particular skill.

The separate meaning check is an engineering safeguard. Related research includes [Chakrabarty, Laban, and Wu on expert editing of model-generated writing](https://arxiv.org/abs/2409.14509) and [Abdulhai and colleagues on changes in meaning and voice during model-assisted revision](https://arxiv.org/abs/2603.18161). Their results motivate careful evaluation; they do not prove that this skill will improve every model or task.
