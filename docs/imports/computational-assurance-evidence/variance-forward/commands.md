# Commands and actual outputs

## SHA-256 command

```sh
shasum -a 256 /private/tmp/brbskills-assurance-import-vcirhv5_/checkout/skills/design-computational-tests/SKILL.md /private/tmp/brbskills-assurance-import-vcirhv5_/checkout/skills/design-computational-tests/tests/fixtures/variance.py /private/tmp/brbskills-assurance-import-vcirhv5_/evidence/variance-forward/run_review.py /private/tmp/brbskills-assurance-import-vcirhv5_/evidence/variance-forward/README.md
```

Exit status: 0

```text
perl: warning: Setting locale failed.
perl: warning: Please check that your locale settings:
	LC_ALL = "C.UTF-8",
	LC_CTYPE = "C.UTF-8",
	LANG = "en_CA.UTF-8"
    are supported and installed on your system.
perl: warning: Falling back to a fallback locale ("en_CA.UTF-8").
fe0a553cf869da4eb5851592e30985e6a96280640248bcbacc8f3cf733ac1e42  /private/tmp/brbskills-assurance-import-vcirhv5_/checkout/skills/design-computational-tests/SKILL.md
62f202525463f6289a90ec495d8b2c2d6137739b3284203fc09aaca3794f039a  /private/tmp/brbskills-assurance-import-vcirhv5_/checkout/skills/design-computational-tests/tests/fixtures/variance.py
8b6c1f6a776f69cebab2f0a7894908cc8505b7b05f9fb5b4e93cf757ee433aa1  /private/tmp/brbskills-assurance-import-vcirhv5_/evidence/variance-forward/run_review.py
0bed63ead311a3a95fe55bfb88cb13fbaea95f9fa6ffe50645baab5fdbc20e14  /private/tmp/brbskills-assurance-import-vcirhv5_/evidence/variance-forward/README.md
```

## Discriminating-check command

```sh
env PYTHONDONTWRITEBYTECODE=1 python3 /private/tmp/brbskills-assurance-import-vcirhv5_/evidence/variance-forward/run_review.py | tee /private/tmp/brbskills-assurance-import-vcirhv5_/evidence/variance-forward/run_review.output.txt
```

Exit status: 0

The actual stdout is preserved verbatim in `run_review.output.txt`:

```text
exact-oracle cases
ordinary symmetric values: values=[-2.0, 0.0, 2.0]
  exact=2.6666666666666665; candidate=2.6666666666666665; match=True
single observation: values=[42.5]
  exact=0.0; candidate=0.0; match=True
large shared offset with representable spacing: values=[1e+16, 1.0000000000000002e+16]
  exact=1.0; candidate=1.8014398509481984e+16; match=False
large finite constant: values=[1e+308, 1e+308]
  exact=0.0; candidate=nan; match=False
metamorphic ordinary-scale cases
translation: baseline=7.46875; translated=7.46875; match=True
scale: baseline_times_9=67.21875; scaled=67.21875; match=True
permutation: baseline=7.46875; reversed=7.46875; match=True
empty input: raised=ValueError; match=True
```

## Final input and evidence hashes

```sh
shasum -a 256 /private/tmp/brbskills-assurance-import-vcirhv5_/checkout/skills/design-computational-tests/SKILL.md /private/tmp/brbskills-assurance-import-vcirhv5_/checkout/skills/design-computational-tests/tests/fixtures/variance.py /private/tmp/brbskills-assurance-import-vcirhv5_/evidence/variance-forward/run_review.py /private/tmp/brbskills-assurance-import-vcirhv5_/evidence/variance-forward/run_review.output.txt /private/tmp/brbskills-assurance-import-vcirhv5_/evidence/variance-forward/README.md /private/tmp/brbskills-assurance-import-vcirhv5_/evidence/variance-forward/commands.md /private/tmp/brbskills-assurance-import-vcirhv5_/evidence/variance-forward/final-response.md | tee /private/tmp/brbskills-assurance-import-vcirhv5_/evidence/variance-forward/input-and-evidence-sha256.txt
```

Exit status: 0. Its stdout is preserved in `input-and-evidence-sha256.txt`:

```text
fe0a553cf869da4eb5851592e30985e6a96280640248bcbacc8f3cf733ac1e42  /private/tmp/brbskills-assurance-import-vcirhv5_/checkout/skills/design-computational-tests/SKILL.md
62f202525463f6289a90ec495d8b2c2d6137739b3284203fc09aaca3794f039a  /private/tmp/brbskills-assurance-import-vcirhv5_/checkout/skills/design-computational-tests/tests/fixtures/variance.py
8b6c1f6a776f69cebab2f0a7894908cc8505b7b05f9fb5b4e93cf757ee433aa1  /private/tmp/brbskills-assurance-import-vcirhv5_/evidence/variance-forward/run_review.py
2aacfc03514457063602cc9b2ab83cb2188adb7ce47baa8f2ba35678bd75094c  /private/tmp/brbskills-assurance-import-vcirhv5_/evidence/variance-forward/run_review.output.txt
0bed63ead311a3a95fe55bfb88cb13fbaea95f9fa6ffe50645baab5fdbc20e14  /private/tmp/brbskills-assurance-import-vcirhv5_/evidence/variance-forward/README.md
a6fb557e21955751845948d2eee5649408f2676ad4eb38e9645b960eb8de3c15  /private/tmp/brbskills-assurance-import-vcirhv5_/evidence/variance-forward/commands.md
e07fa1b4f82bf78099cca5f48ccb119d40c1ec6435716a3b2c3ea08d9996f3e4  /private/tmp/brbskills-assurance-import-vcirhv5_/evidence/variance-forward/final-response.md
```
