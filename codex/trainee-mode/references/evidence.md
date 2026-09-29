# Rationale and experimental status

This protocol is an experimental teaching design. No study establishes that this
skill improves fMRI judgment, retention, independent execution, or transfer.
Repository checks establish packaging consistency only. The fixed checkpoint
sequence and hint ladder are design choices, not a validated tutoring algorithm.

- [Bainbridge (1983), Ironies of automation](https://doi.org/10.1016/0005-1098(83)90046-8),
  especially sections 2.3 and 3.1–3.4: motivates maintaining practice, feedback,
  and understanding. She cautions against adapting aid solely to overall skill
  and describes reduced problem-solving effectiveness under time pressure.
  Her discussion of Craik concerns processing for meaning; it does not establish
  that discovering every answer is better than receiving instruction.
- [Kalyuga et al. (2003), The expertise reversal effect](https://doi.org/10.1207/S15326985EP3801_4):
  supports considering prior knowledge when providing guidance. It does not
  validate this skill's checkpoint selection or support ladder.
- [Roediger and Karpicke (2006), Test-enhanced learning](https://doi.org/10.1111/j.1467-9280.2006.01693.x):
  recall practice improved delayed retention of studied prose. Reflection about
  an analysis is not automatically a retrieval task, and scientific transfer
  remains a separate outcome to test.
- [Bastani et al. (2025), Generative AI without guardrails can harm learning](https://doi.org/10.1073/pnas.2422633122):
  in high-school mathematics, assisted practice improved but GPT Base users
  performed worse when assistance was removed. GPT Tutor safeguards largely
  mitigated that harm; the study did not demonstrate an unaided benefit over
  control for that tutor. This is motivation to evaluate, not fMRI validation.

Future evaluation should separate protocol adherence from human learning:
first exercise representative interactions, then compare later unaided work on
unfamiliar tasks with an appropriate baseline and independent grading. Include
time, support required, error detection, and false alarms. See the
[unrun behavioral cases](../tests/evaluation-cases.md); no evaluation framework
or human study is bundled.
