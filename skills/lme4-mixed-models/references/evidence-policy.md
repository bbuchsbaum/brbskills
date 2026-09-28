# Evidence policy and adjudication

## What this collection claims

This is a broad, targeted scoping synthesis assembled on **2026-09-25**. It is not an exhaustive systematic review, an expert-panel guideline, a citation-count vote, or a statement that the named authors approved this skill. It covers frequentist Gaussian and generalized mixed models centered on lme4; simulation findings are not automatically transferable across families and designs.

Search paths combined official lme4/companion-package documentation, exact-title searches for methodological papers, and named-author blog/forum discussions. Selection favored original method developers, peer-reviewed methods and simulations, reproducible examples, and explicit discussion of assumptions. Sources were followed across the maximality debate, inference, model checking, contrasts, and reporting. Some papers were accessible only as abstracts or author/institutional records: these are identified in the registry and used only for narrow, supported claims. No paywalled full text is claimed to have been read.

## Labels used in this skill

**Implementation** means a documented behavior of a particular package/API, to be checked locally. **Broad agreement** means a robust principle supported across consulted sources, not a quantified community survey. **Disputed** identifies credible competing recommendations. **Policy** is this bundle's operational choice. **Derived** denotes a mathematical consequence explained here rather than an attributed empirical finding.

| Claim or decision | Label | Basis and boundary |
|---|---|---|
| Respect crossed sampling units and design-supported slopes | Broad agreement | MAX, INT, LMM-PAPER; exact covariance complexity is disputed. |
| Always keep maximal covariance | Disputed | MAX favors maximal confirmatory structures; PARS/POWER emphasize supported complexity and power. |
| Singularity differs from optimizer failure | Implementation + broad agreement | SING, CONV; neither is a model-adequacy verdict. |
| Use ML when comparing different fixed-effect spaces by likelihood | Implementation/statistical requirement | LMM, PB; does not prohibit appropriate REML-based tests. |
| Every LMM has one exact denominator df | Rejected | PV, SAT, KR; approximations have different scopes. |
| LMM small-sample methods solve sparse GLMM inference | Rejected | PV, KR, LUKE; Gaussian results are not generic GLMM guarantees. |
| Diagonal random covariance survives every recoding | Rejected; derived | Algebra in design-random-effects.md; free covariance and constrained covariance behave differently. |
| A finite optimizer-rescue budget and explicit blocked states | Policy | Engineering guardrails, not literature constants. |
| Change formulas until significance appears | Rejected policy | Selection target and disclosure requirements in inference-selection.md. |
| New-group marginal mean equals inverse-link at zero RE | Rejected; derived | PRED, ETRANS; nonlinear averaging distinction. |

## The random-effects disagreement, represented fairly

**Barr et al. (2013) [MAX]** argue that confirmatory testing should represent design-justified subject/item variability, with simulations supporting maximal structures against anticonservative alternatives. Do not misread the position as adding slopes for variables that cannot vary within a group or fitting every conceivable term.

**Bates et al. (2015) [PARS]** propose diagnosing unsupported covariance dimensions, including PCA-based examination, and fitting parsimonious structures. This source is an author preprint, not a journal article.

**Matuschek et al. (2017) [POWER]** study the Type-I-error/power balance in particular crossed Gaussian simulations. Data-supported simplification can help power under their conditions. Their selection threshold is not a universal rule for arbitrary experiments, small clusters, or GLMMs; the study's handling of nonconvergent simulated fits also limits extrapolation.

**lme4's singularity documentation [SING]** explicitly presents multiple approaches without declaring consensus. The skill therefore requires a policy declaration, protects essential variation, and asks for sensitivity—not allegiance to a slogan. This is the central synthesis decision.

## How to use forums and blogs

Named experts' original explanations can clarify practical failures, historical API behavior, or scientific interpretation. They do not establish error-rate control. Bolker's r-sig-mixed-models replies [FORUM-DF; FORUM-NUM] clarify denominator-df differences and numerical troubleshooting. Morey's essay [BLOG-P] supplies an explicitly authored interpretation of significance-focused practice. Gelman's discussion [BLOG-C] points to the substantive meaning of centering; individual comments are attributed to their authors, not to Gelman.

Do not infer truth from votes, a familiar name alone, or an accepted answer. This review did not adopt forum shortcuts equating singularity with fixed-design collinearity, treating all likelihood tests as interchangeable, or turning off warnings as a remedy.

## Maintenance and escalation

When installed help conflicts with a dated example, check the installed source/help and current official documentation. Keep the scientific rule separate from the changing API. Log any override with question, evidence, scope, and effect on inference. A new version should recheck links, rerun R tests, and rerun agent scenarios. An agent must not call an unreviewed addition “community consensus.”
