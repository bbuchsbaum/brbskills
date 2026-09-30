# Sources, authority and scope

Sources reviewed 2026-09-30; URLs resolved and bibliographic details were checked against Crossref on that date. This skill is an independent implementation, not an OHBM product, endorsement, certification or revised COBIDAS standard. No third-party full text or software is redistributed.

## Baseline and crosswalk

The baseline is the final **OHBM COBIDAS MRI report v1.0, 2016-05-19** [C1], not the earlier "proposed" version circulated for community comment. Appendix C gives short descriptions of task-fMRI and ICA models for specific software versions of that time; Appendix D contains seven tables of reporting items, each marked mandatory (Y) or not (N). The local field catalogue groups operational facts; its IDs, profile applicability and `required` flags are local and must not be presented as official row IDs or mandatory designations.

| Official table (printed pages in [C1]) | Local reporting route |
|---|---|
| D.1 Experimental design, pp. 44–48 | [design-acquisition.md](design-acquisition.md): participants, flow, ethics, task, power |
| D.2 Acquisition, pp. 48–52 | [design-acquisition.md](design-acquisition.md): scanner, sequences, timing, variants, acquisition QC |
| D.3 Preprocessing, pp. 53–58 | [preprocessing-qc.md](preprocessing-qc.md); diffusion/perfusion rows in [structural-diffusion.md](structural-diffusion.md) |
| D.4 Statistical modelling and inference, pp. 59–67 | [models-inference.md](models-inference.md), [connectivity.md](connectivity.md), [multivariate-rsa.md](multivariate-rsa.md) |
| D.5 Results, pp. 67–69 | [models-inference.md](models-inference.md#results-connection) and the connectivity/multivariate modules |
| D.6 Data sharing, pp. 69–70 | [writing.md](writing.md): materials, access, ethics of sharing, identifiers |
| D.7 Reproducibility, p. 71 | [evidence.md](evidence.md) and [writing.md](writing.md): tools, infrastructure, workflow, provenance |

A full official audit uses `assets/official-checklist-template.tsv`. For each applicable row record table, page and aspect label, the mandatory designation as printed, applicability and reason, evidence or fact IDs, and manuscript location. Split rows with several subrequirements when needed. Local row keys are not published identifiers. Field coverage from the helper does not complete this process.

The report already covers multivariate and predictive modelling, including searchlight and RSA [C1]. This skill adds finer records for fitted transforms, modern features, RSA dependencies and agent decisions, plus planned-versus-actual state, receipts, hashes, concurrency, stale-draft detection and evidence-bound writing. These are local extensions.

## Scope beyond MRI

EEG and MEG have a separate OHBM COBIDAS MEEG report [C5]; this skill does not implement it. ASL and DSC perfusion rows exist in D.2/D.3 but are not modelled in the local catalogue; spectroscopy, quantitative MRI and PET need modality-specific guidance.

## Primary sources

**[C1]** Nichols TE, Das S, Eickhoff SB, et al. *Best Practices in Data Analysis and Sharing in Neuroimaging using MRI*. OHBM COBIDAS report v1.0, 2016-05-19. https://www.humanbrainmapping.org/files/2016/COBIDASreport.pdf (preprint: bioRxiv, https://doi.org/10.1101/054262)

**[C2]** Nichols TE, Das S, Eickhoff SB, et al. (2017). Best practices in data analysis and sharing in neuroimaging using MRI. *Nature Neuroscience* 20, 299–303. https://doi.org/10.1038/nn.4500. Journal summary; the checklist is in [C1].

**[C3]** INCF COBIDAS resource and the INCF/OHBM eCOBIDAS working group. https://www.incf.org/cobidas; https://www.incf.org/sig/incfohbm-working-group-checklists-transparent-methods-reporting-neuroscience-ecobidas

**[C4]** eCOBIDAS: structured checklists and methods generation. https://ecobidas.readthedocs.io/en/latest/; https://github.com/ohbm/eCobidas. No compatibility with its export schemas is claimed.

**[C5]** Pernet C, Garrido MI, Gramfort A, et al. (2020). Issues and recommendations from the OHBM COBIDAS MEEG committee for reproducible EEG and MEG research. *Nature Neuroscience* 23, 1473–1483. https://doi.org/10.1038/s41593-020-00709-0

**[B1]** BIDS specification, *Common principles* (inheritance). The stable documentation resolved to 1.11.1 at the 2026-09-29 review. https://bids-specification.readthedocs.io/en/stable/common-principles.html

**[B2]** BIDS specification, *Magnetic Resonance Imaging*: timing units, `SliceTiming`, `VolumeTiming`, discarded volumes, phase-encoding axes, field-map associations and sequence metadata. https://bids-specification.readthedocs.io/en/stable/modality-specific-files/magnetic-resonance-imaging-data.html

**[B3]** BIDS specification, *Dataset description*: `GeneratedBy`, `SourceDatasets` and derivative provenance. https://bids-specification.readthedocs.io/en/stable/modality-agnostic-files/dataset-description.html

**[F1]** fMRIPrep, *Outputs of fMRIPrep*: layout, confounds, CompCor/cosine coupling, outlier defaults. Use the documentation for the executed version. https://fmriprep.org/en/stable/outputs.html (command-line options: https://fmriprep.org/en/stable/usage.html)

**[F2]** NiPreps, *Transparency of workflows*: methods/citation boilerplate. https://www.nipreps.org/intro/transparency/

**[A1]** AFNI, `3dTproject` help: joint projection and censor modes. https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTproject.html

**[A2]** AFNI, `afni_proc.py` documentation. Live documentation is not the executed version. https://afni.nimh.nih.gov/pub/dist/doc/htmldoc/programs/alpha/afni_proc.py_sphx.html

**[K1]** Kriegeskorte N, Simmons WK, Bellgowan PSF, Baker CI (2009). Circular analysis in systems neuroscience: the dangers of double dipping. *Nature Neuroscience* 12, 535–540. https://doi.org/10.1038/nn.2303

**[E1]** Eklund A, Nichols TE, Knutsson H (2016). Cluster failure: why fMRI inferences for spatial extent have inflated false-positive rates. *PNAS* 113, 7900–7905. https://doi.org/10.1073/pnas.1602413113

**[L1]** Lindquist MA, Geuter S, Wager TD, Caffo BS (2019). Modular preprocessing pipelines can reintroduce artifacts into fMRI data. *Human Brain Mapping* 40, 2358–2376. https://doi.org/10.1002/hbm.24528

**[M1]** scikit-learn, *Common pitfalls and recommended practices*: data leakage and fit boundaries. General discipline, not a neuroimaging standard. https://scikit-learn.org/stable/common_pitfalls.html

**[P1]** W3C, *PROV Overview*. The local JSON format mirrors the entity/activity/agent distinction; it is not a validated PROV, NIDM or BIDS serialization. https://www.w3.org/TR/prov-overview/

## Maintenance policy

Keep the scientific baseline pinned until a deliberate review. Put version-specific tool behaviour in the relevant module with the version it was checked against, rather than treating current defaults as universal. Record source changes, update the catalogue, and rerun tests and evaluations before release. Never relabel this skill as a new official COBIDAS edition.
