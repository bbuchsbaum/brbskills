# Source registry

48 selected sources; original 44 verified/consulted 2026-09-25, four audit/inference additions consulted 2026-09-27. A targeted scoping collection, not a systematic-review census. Source IDs in the skill resolve here. Access descriptions distinguish full help/manuscript sections from abstracts and excerpts. Publisher DOIs identify sources even when access was via an author manuscript or index.

Filter `sources.json` by ID for machine-readable, token-light retrieval. No full-text articles are redistributed.

## LMM
**lme4 authors (living documentation). Fit Linear Mixed-Effects Models — lmer.**
[official documentation](https://lme4.github.io/lme4/reference/lmer.html)
Consulted: Relevant full help sections. Use: Formula syntax, numeric-only double-bar caveat, rank loss, weights, REML. Limitation: Site displayed a development version; inspect installed help.

## GLMM
**lme4 authors (living documentation). Fitting Generalized Linear Mixed-Effects Models — glmer.**
[official documentation](https://lme4.github.io/lme4/reference/glmer.html)
Consulted: Relevant full help sections. Use: Conditional families, likelihood integration, nAGQ limitations. Limitation: Do not extend higher quadrature to unsupported random structures.

## CONV
**lme4 authors (living documentation). Assessing Convergence for Fitted Models.**
[official documentation](https://lme4.github.io/lme4/reference/convergence.html)
Consulted: Full guidance consulted. Use: Numerical triage, optimizer controls, allFit, derivative diagnostics. Limitation: Practical optimizer agreement is not model adequacy.

## SING
**lme4 authors (living documentation). Test Fitted Model for (Near) Singularity — isSingular.**
[official documentation](https://lme4.github.io/lme4/reference/isSingular.html)
Consulted: Full guidance consulted. Use: Boundary covariance, rePCA, explicitly unresolved strategy debate. Limitation: Tolerance is numerical; no universal selection strategy is endorsed.

## PV
**lme4 authors (living documentation). Getting p-values for fitted models.**
[official documentation](https://lme4.github.io/lme4/reference/pvalues.html)
Consulted: Full guidance consulted. Use: Available inferential routes and Gaussian/GLMM distinctions. Limitation: A methods menu, not a universal validity guarantee.

## BOOT
**lme4 authors (living documentation). Model-based (Semi-)Parametric Bootstrap — bootMer.**
[official documentation](https://lme4.github.io/lme4/reference/bootMer.html)
Consulted: Relevant full help sections. Use: Simulation conditioning and failure diagnostics. Limitation: Bootstrap targets and failed refits require explicit review.

## PRED
**lme4 authors (living documentation). Predictions from a model at new data values — predict.merMod.**
[official documentation](https://lme4.github.io/lme4/reference/predict.merMod.html)
Consulted: Relevant full help sections. Use: re.form, new levels, prediction uncertainty limitations. Limitation: Software population-level terminology may mean random effects zero.

## SIM
**lme4 authors (living documentation). Simulate Responses From merMod Object.**
[official documentation](https://lme4.github.io/lme4/reference/simulate.merMod.html)
Consulted: Relevant full help sections. Use: Conditional versus resimulated random effects. Limitation: Simulation and prediction use re.form for related but distinct operations.

## CI
**lme4 authors (living documentation). Compute Confidence Intervals for Parameters of a [ng]lmer Fit.**
[official documentation](https://lme4.github.io/lme4/reference/confint.merMod.html)
Consulted: Relevant full help sections. Use: Profile, Wald, and parametric-bootstrap intervals. Limitation: Wald intervals do not cover covariance parameters here; BCa/studentized bootstrap choices are not supported.

## NB
**lme4 authors (living documentation). Fitting Negative Binomial GLMMs — glmer.nb.**
[official documentation](https://lme4.github.io/lme4/reference/glmer.nb.html)
Consulted: Full help consulted. Use: Negative-binomial theta versus random-covariance theta. Limitation: Dispersion-parameter inference has documented limitations.

## LMM-PAPER
**Bates, Mächler, Bolker, Walker (2015). Fitting Linear Mixed-Effects Models Using lme4.**
[peer-reviewed methods paper](https://www.jstatsoft.org/article/view/v067i01)
Consulted: Publisher abstract/metadata; implementation details checked against current help. Use: Reference implementation and model architecture. Limitation: Journal of Statistical Software 67(1); DOI 10.18637/jss.v067.i01. Full paper not claimed read.

## MAX
**Barr, Levy, Scheepers, Tily (2013). Random effects structure for confirmatory hypothesis testing: Keep it maximal.**
[peer-reviewed simulation/methods paper](https://doi.org/10.1016/j.jml.2012.11.001)
Consulted: Publisher/PubMed abstract and source cross-checks; full PMC page blocked. Use: Primary design-maximal position in the debate. Limitation: Do not attribute detailed simulation settings not inspected; DOI identifies the primary paper.

## PARS
**Bates, Kliegl, Vasishth, Baayen (2015). Parsimonious Mixed Models.**
[author preprint](https://arxiv.org/html/1506.04967)
Consulted: Full HTML, relevant sections. Use: PCA and supported covariance complexity. Limitation: Preprint arXiv:1506.04967, not presented as a peer-reviewed journal paper.

## POWER
**Matuschek, Kliegl, Vasishth, Baayen, Bates (2017). Balancing Type I error and power in linear mixed models.**
[peer-reviewed simulation/methods paper](https://arxiv.org/html/1511.01864)
Consulted: Full author-manuscript HTML, relevant sections. Use: Model complexity, power, and selection in crossed Gaussian simulations. Limitation: Published DOI 10.1016/j.jml.2017.01.001; study-specific designs/selection thresholds and handling of nonconvergence limit generalization.

## INT
**Dale J. Barr (2013). Random effects structure for testing interactions in linear mixed-effects models.**
[peer-reviewed methods paper](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2013.00328/full)
Consulted: Full HTML, relevant sections. Use: Random slopes relevant to interaction tests. Limitation: Design-specific reasoning, not every possible slope under every grouping factor.

## CENTER
**Craig K. Enders and Davood Tofighi (2007). Centering predictor variables in cross-sectional multilevel models: A new look at an old issue.**
[peer-reviewed methods paper](https://doi.org/10.1037/1082-989X.12.2.121)
Consulted: Abstract and author-uploaded full-text excerpt via ResearchGate. Use: Within/between interpretation and meaningful centering. Limitation: Primary scope is cross-sectional two-level models, not a universal longitudinal or causal recipe.

## CONTR
**Schad, Vasishth, Hohenstein, Kliegl (2020). How to capitalize on a priori contrasts in linear (mixed) models: A tutorial.**
[peer-reviewed methods tutorial](https://arxiv.org/html/1807.10451)
Consulted: Full author-manuscript HTML, relevant sections. Use: Hypothesis-driven contrasts and coding. Limitation: Published DOI 10.1016/j.jml.2019.104038; code basis/hypothesis must still match the analysis.

## SAT
**Kuznetsova, Brockhoff, Christensen (2017). lmerTest Package: Tests in Linear Mixed Effects Models.**
[peer-reviewed software/methods paper](https://www.jstatsoft.org/v82/i13/)
Consulted: Publisher abstract and package-author documentation. Use: Satterthwaite and related tests for Gaussian LMMs. Limitation: Not a generic glmer finite-sample correction.

## SAT-API
**Rune Haubo B. Christensen (living documentation). Coerce lmerMod Objects to lmerModLmerTest.**
[official documentation](https://search.r-project.org/CRAN/refmans/lmerTest/html/as_lmerModLmerTest.html)
Consulted: Full help consulted. Use: Explicit wrapper conversion without search-path masking. Limitation: The mirror displayed version 3.1-3; use installed API documentation.

## KR
**pbkrtest authors (living documentation). Kenward-Roger-based comparison of models — kr-modcomp.**
[official documentation](https://hojsgaard.github.io/pbkrtest/reference/kr-modcomp.html)
Consulted: Relevant full help sections. Use: Gaussian-model KR comparison and supported model requirements. Limitation: Check same covariance structure and fixed-effect restrictions; not universal GLMM support.

## PB
**pbkrtest authors (living documentation). Model comparison using parametric bootstrap methods — pb-modcomp.**
[official documentation](https://hojsgaard.github.io/pbkrtest/reference/pb-modcomp.html)
Consulted: Full relevant help sections. Use: Null simulation, ML refitting, lmer/glmer support, negative LR diagnostics. Limitation: Review actual reference sample counts and numerical failures.

## KR-PAPER
**Halekoh and Højsgaard (2014). A Kenward-Roger Approximation and Parametric Bootstrap Methods for Tests in Linear Mixed Models — The R Package pbkrtest.**
[peer-reviewed software/methods paper](https://www.jstatsoft.org/article/view/v059i09)
Consulted: Publisher abstract/metadata; current package help checked separately. Use: Original companion inference-method implementation. Limitation: Journal of Statistical Software 59(9); do not infer current GLMM support from the original Gaussian title alone.

## RLR
**Fabian Scheipl and RLRsim contributors (living documentation). Restricted Likelihood Ratio Tests — exactRLRT.**
[official documentation](https://search.r-project.org/CRAN/refmans/RLRsim/html/exactRLRT.html)
Consulted: Full relevant help sections. Use: Supported finite-sample restricted variance-component tests. Limitation: Known correlation structure, iid errors, and additional restrictions; not arbitrary covariance testing.

## LUKE
**Steven G. Luke (2017; online 2016). Evaluating significance in linear mixed-effects models in R.**
[peer-reviewed simulation study](https://doi.org/10.3758/s13428-016-0809-y)
Consulted: PubMed and publisher abstract; full body not accessible. Use: Comparison of significance approximations in studied Gaussian designs. Limitation: Findings are simulation-specific, not proof for all group sizes or GLMMs.

## REPORT
**Lotte Meteyard and Robert A. I. Davies (2020). Best practice guidance for linear mixed-effects models in psychological science.**
[peer-reviewed practice review](https://doi.org/10.1016/j.jml.2020.104092)
Consulted: Author/institutional abstract and author-uploaded excerpts. Use: Variation in analysis/reporting practice; reproducibility rationale. Limitation: Detailed recommendations not treated as fully inspected journal text.

## ECO
**Xavier A. Harrison et al. (2018). A brief introduction to mixed effects modelling and multi-model inference in ecology.**
[peer-reviewed methods review](https://doi.org/10.7717/peerj.4794)
Consulted: Abstract and author-uploaded text excerpts. Use: Ecology perspective on models, assumptions, and information-theoretic comparison. Limitation: Broader perspective, not a primary experiment establishing every rule in this skill.

## CV
**David R. Roberts et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure.**
[peer-reviewed methodological paper](https://doi.org/10.1111/ecog.02881)
Consulted: Search-indexed abstract/metadata and author-institution record. Use: Structured validation and generalization targets. Limitation: Detailed crossed subject-item splitting in this skill is a derived operational application.

## ESIZE
**Marc Brysbaert (2025). How to Run Linear Mixed Effects Analysis for Pairwise Comparisons? A Tutorial and a Proposal for the Calculation of Standardized Effect Sizes.**
[peer-reviewed tutorial/proposal](https://journalofcognition.org/articles/10.5334/joc.409)
Consulted: Full HTML available; title/scope and relevant sections consulted. Use: Recent effect-size proposal and pairwise-analysis tutorial. Limitation: A proposal is not consensus on a universal mixed-model effect size.

## FAQ
**Ben Bolker and contributors (living document; visible revision 2025-07-19). GLMM FAQ.**
[expert technical reference](https://bbolker.github.io/mixedmodels-misc/glmmFAQ.html)
Consulted: Full HTML, selected relevant sections. Use: Broad specialist routing reference for mixed-model pitfalls. Limitation: Expert maintained, not a peer-reviewed consensus guideline; consult cited original sources for contested details.

## DHARMA
**Florian Hartig and DHARMa contributors (living documentation). DHARMa reference manual: simulateResiduals, testDispersion, and related diagnostics.**
[official documentation](https://cran.r-project.org/web/packages/DHARMa/refman/DHARMa.html)
Consulted: Relevant full manual sections. Use: Simulation-residual settings, 0.5.0 default change, diagnostic interpretation. Limitation: Check installed API/defaults; not all conditional modes are supported for every model engine.

## TROUBLE
**glmmTMB authors (living documentation). Troubleshooting with glmmTMB.**
[official documentation](https://cran.r-project.org/web/packages/glmmTMB/vignettes/troubleshooting.html)
Consulted: Relevant full vignette sections. Use: Separation, weak information, Hessians, and model complexity. Limitation: Engine-specific implementation; cross-engine statistical lessons are distinguished from syntax.

## COV
**glmmTMB authors (living documentation). Covariance structures with glmmTMB.**
[official documentation](https://glmmtmb.github.io/glmmTMB/articles/covstruct.html)
Consulted: Relevant full vignette sections. Use: Alternative structured covariance models and their parameterizations. Limitation: An engine-routing reference, not a drop-in lme4 recipe.

## EBASIC
**Russell V. Lenth and emmeans contributors (living documentation). Basics of estimated marginal means.**
[official documentation](https://rvlenth.github.io/emmeans/articles/basics.html)
Consulted: Relevant full vignette sections. Use: Reference grids and deliberate weighting. Limitation: Marginal means terminology does not itself specify random-effect integration.

## EINT
**Russell V. Lenth and emmeans contributors (living documentation). Interaction analysis in emmeans.**
[official documentation](https://rvlenth.github.io/emmeans/articles/interactions.html)
Consulted: Relevant full vignette sections. Use: Simple comparisons, trends, and interactions. Limitation: Avoid unjustified averaging over moderators.

## ETRANS
**Russell V. Lenth and emmeans contributors (living documentation). Transformations and link functions in emmeans.**
[official documentation](https://rvlenth.github.io/emmeans/articles/transformations.html)
Consulted: Relevant full vignette sections. Use: Regridding, order of averaging/transformation, bias adjustment. Limitation: Back-transformation is not automatically full new-group marginalization.

## ECOMP
**Russell V. Lenth and emmeans contributors (living documentation). Comparisons and contrasts in emmeans.**
[official documentation](https://rvlenth.github.io/emmeans/articles/comparisons.html)
Consulted: Relevant full vignette sections. Use: Comparison families, adjustments, and contrast interpretation. Limitation: Check actual p-value and interval adjustments in returned output.

## ESOPH
**Russell V. Lenth and emmeans contributors (living documentation). Models supported by emmeans: sophisticated models.**
[official documentation](https://rvlenth.github.io/emmeans/articles/sophisticated.html)
Consulted: Relevant full vignette sections. Use: LMM df methods and covariance adjustments. Limitation: Dependencies/size limits can change the method actually used.

## EMESSY
**Russell V. Lenth and emmeans contributors (living documentation). Working with messy data.**
[official documentation](https://rvlenth.github.io/emmeans/articles/messy-data.html)
Consulted: Relevant full vignette sections. Use: Nesting, confounding, nonestimability. Limitation: No software grid can recover an unidentified contrast without additional assumptions.

## FORUM-DF
**Ben Bolker; thread includes Jake Westfall (2015-07-07). lme and lmer degrees of freedom (and hence p values).**
[named-expert forum reply](https://stat.ethz.ch/pipermail/r-sig-mixed-models/2015q3/023757.html)
Consulted: Full archived message. Use: Original expert clarification of package df behavior. Limitation: Historical discussion: confirm present package behavior separately.

## FORUM-NUM
**Ben Bolker (2018-07-20). Downdated VtV is not positive definite.**
[named-expert forum reply](https://stat.ethz.ch/pipermail/r-sig-mixed-models/2018q3/027015.html)
Consulted: Full archived message. Use: Concrete numerical-debugging context. Limitation: An example diagnosis, not a universal explanation for this error.

## BLOG-P
**Richard Morey (2017-07-06). Putting p’s into lmer: mixed-model regression and statistical significance.**
[named-author blog/essay](https://featuredcontent.psychonomic.org/putting-ps-into-lmer-mixed-model-regression-and-statistical-significance/)
Consulted: Full essay consulted. Use: Original interpretation of significance-focused practice. Limitation: Luke is the primary source for simulation results; the Society does not endorse all contributor opinions.

## BLOG-C
**Andrew Gelman; separately attributed commenters (2022-12-04). Centering predictors in Bayesian multilevel models.**
[named-author blog/discussion](https://statmodeling.stat.columbia.edu/2022/12/04/centering-predictors-in-bayesian-multilevel-models/)
Consulted: Full post and relevant comments. Use: Substantive centering discussion and primary-source routes. Limitation: Quoted questions and comments are not automatically the post author’s endorsed conclusions.

## CODEX
**OpenAI (living documentation). Build skills / Codex skills documentation.**
[official product documentation](https://developers.openai.com/codex/skills/)
Consulted: Current page followed through official redirect. Use: SKILL.md progressive disclosure and .agents/skills placement. Limitation: Installation paths can evolve; check current official documentation.

## CLAUDE
**Anthropic (living documentation). Extend Claude with skills.**
[official product documentation](https://code.claude.com/docs/en/skills)
Consulted: Relevant full documentation sections. Use: SKILL.md structure and .claude/skills placement. Limitation: No vendor-specific tool permission settings are included in this portable bundle.

## VCOV
**lme4 authors (living documentation). Covariance matrix of estimated parameters — vcov.merMod.**
[official documentation](https://lme4.github.io/lme4/reference/vcov.merMod.html)
Consulted 2026-09-27: Relevant arguments and details; installed lme4 2.0.1 method inspected. Use: Hessian versus RX covariance and documented fallback/accuracy limitations. Limitation: Availability and fallback behavior are version-sensitive; neither method certifies coverage.

## PERF
**lme4 authors (living documentation). lme4 performance tips.**
[official documentation](https://lme4.github.io/lme4/articles/lmerperf.html)
Consulted 2026-09-27: Derivative-cost section. Use: Post-fit finite-difference cost grows quadratically in top-level parameter count. Limitation: Exact evaluation counts and wall-clock cost depend on implementation and model; benchmark locally.

## LME4-NEWS
**lme4 authors (living documentation). lme4 changelog.**
[official documentation](https://lme4.github.io/lme4/news/index.html)
Consulted 2026-09-27: Singular-fit convergence-check entry; installed lme4 2.0.1 optwrap/checkConv also inspected. Use: Convergence checks can be skipped for singular fits; controls are not completion evidence. Limitation: Historical changelog is not a complete account of every installed version or control path.

## PADJUST
**R Core Team (living documentation). Adjust P-values for Multiple Comparisons.**
[official documentation](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/p.adjust.html)
Consulted 2026-09-27: Arguments and Details. Use: Holm family-wise adjustment and distinction from interval coverage. Limitation: Multiplicity adjustment assumes valid component tests; it does not repair their approximation or model.
