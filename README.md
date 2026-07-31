# Proto-Elamite arithmetic replication

An independent, deterministic reimplementation of published computational
results on the proto-Elamite corpus, with exploratory tests of arithmetic
closure.

This is **not a decipherment project**. It does not ask a model to interpret
signs, guess meanings, or translate texts. Parsing, numeral conversion,
constraint checks, and permutation tests are ordinary seeded Python code.

## Status and scope

This repository is a reimplementation and a set of open questions, not a
result. Specifically:

- It **does not** claim to replicate the 24 disambiguated texts reported by
  Born et al. (2023). Set identity is unverified and the procedures differ.
- It **does not** claim to validate or invalidate the published method.
- The permutation analyses below are **exploratory**. Definitions and null
  designs were arrived at through a sequential process in which earlier
  results were visible. Decision rules were written down before each
  computation, which is documented in `NOTES.md`, but this is not
  preregistration and the p-values should not be read as calibrated error
  rates.

What the repository does offer: an independently written parser and numeral
converter, a test suite locking in the published figures, a measured set of
deltas against a more recent corpus snapshot, and permutation machinery that
did not previously exist for this corpus.

An earlier version of this README made stronger claims. Those claims did not
survive external review and have been removed. The reasoning that produced
them, including the errors, remains in `NOTES.md`.

## Reproduce it

Requirements:

- Python 3.11 or later
- [`uv`](https://docs.astral.sh/uv/)
- Git with submodule support

```
git clone --recurse-submodules https://github.com/NicolasMasselot/proto-elamite.git
cd proto-elamite
uv sync
uv run pytest -q
```

The test suite currently contains 34 tests and runs in under a minute on a
laptop. It requires no GPU, API key, or network access after the repository
and submodule have been cloned.

The corpus is [`sfu-natlang/pe-headers`](https://github.com/sfu-natlang/pe-headers), pinned as a
submodule at:

```
88948d18f3d9c0250c33344fd9e6c8968438869f
```

That snapshot is dated **2023-02-09**, roughly four months after the
2022-10-03 corpus download documented in the paper. It is not the current CDLI
state, and the differences reported below may reflect either snapshot drift or
implementation divergence. They are reported, not attributed.

Every random process uses the fixed seed `20260727`.

## Replication of published figures

These are the solid part of this repository. They are measured directly
against published numbers and do not depend on any modelling choice.

### Corpus inventory

| Figure                    | Published | This snapshot | Delta |
| ------------------------- | --------- | ------------- | ----- |
| Raw texts                 | 1,467     | 1,467         | 0     |
| Cleaned texts             | 1,399     | 1,398         | -1    |
| Entries                   | 11,013    | 11,026        | +13   |
| Tokens                    | 33,778    | 33,828        | +50   |
| Broken or unreadable      | 7,508     | 7,584         | +76   |
| Numerals                  | 11,364    | 11,389        | +25   |
| Non-numerical tokens      | 14,906    | 14,855        | -51   |
| Non-numerical types       | 1,623     | 1,630         | +7    |
| Hapax non-numerical types | 745       | 744           | -1    |

Damage is retained rather than discarded. The parser distinguishes an
identified but broken sign, an unreadable sign, and a missing sign.

### Numeral conversion

Numerals are converted under the decimal (D), sexagesimal (S),
bisexagesimal (B), and capacity (C) systems using Algorithm 1 and Figure 1
from the corrected revision of Born et al.,
[arXiv:2502.00090v2](https://arxiv.org/abs/2502.00090).

| Valid systems    | Published | This snapshot | Delta |
| ---------------- | --------- | ------------- | ----- |
| None             | 27        | 49            | +22   |
| B                | 18        | 15            | -3    |
| C                | 1,678     | 1,743         | +65   |
| D                | 96        | 78            | -18   |
| S                | 107       | 106           | -1    |
| B \| D           | 22        | 21            | -1    |
| B \| S           | 5         | 5             | 0     |
| C \| D           | 49        | 46            | -3    |
| C \| S           | 143       | 146           | +3    |
| B \| C \| S      | 185       | 177           | -8    |
| B \| D \| S      | 292       | 291           | -1    |
| B \| C \| D \| S | 5,389     | 5,331         | -58   |

Summary:

- Intact notations: 8,008 observed versus 8,011 published (`-3`)
- At least one valid reading: 7,959 versus 7,984 (`-25`)
- Unambiguous readings: 1,942 versus 1,899 (`+43`)

Two deltas here may be worth the authors' attention. The invalid count is
**49 against 27 published**, and unambiguous readings number **1,942 against
1,899**. The invalid notations are documented rather than normalized away:
they include Figure-1-absent signs (N02 in 22 cases, N51G in 6, N39A in 4),
over-counts before carrying, and mixed-system sequences. No aliases or carry
limits were added to reduce these deltas.

The `+43` on unambiguous readings is not small relative to the downstream
analysis, which turns on the presence of unambiguous notations in tablets
numbering in the tens.

## Closure implementation

The paper's method is a **subset-sum** search: it asks whether any combination
of obverse readings equals any reading of the reverse under one consistent
system. Candidates are then retained after manual inspection by domain
experts. The paper reports **24 texts**; the pre-inspection count and the 24
P-numbers are not published.

This repository implements the subset-sum rule and, separately, a stricter
full-sum variant.

| Definition                          | Raw closures (of 425 candidates) | With an unambiguous witness |
| ----------------------------------- | -------------------------------- | --------------------------- |
| Subset sum (the published method)   | 151                              | 52                          |
| Full sum (a stricter variant, ours) | 63                               | 21                          |

**The full-sum rule is not the published method.** It was introduced here
after reading the paper's description of tablet P008014, where all entries
happen to participate. That description characterises one tablet, not the
general algorithm. The full-sum numbers are reported only as a diagnostic on
how sensitive the outcome is to search permissiveness. The numerical proximity
of 21 to the published 24 is unexplained and is not a replication: the
procedures differ, and set identity is unknown because the 24 P-numbers are
unpublished.

Of the 15 tablets cited in the paper's Appendix A, 3 appear in the subset-sum
witness set here (P008014, P008173, P008243). Most of the remainder were
disambiguated in the paper by evidence other than subset-sum, chiefly the
2.5:1 ratio of M056~f to M288, so their absence is expected rather than a
failed check.

The 425-candidate filter (tablets with one or two reverse entries) follows a
heuristic described in the paper rather than a formally stated rule.

The "unambiguous witness" condition is this repository's formalization of the
paper's evidentiary criterion, requiring that a closure contain at least one
intrinsically unambiguous notation. It has not been confirmed with the authors
and may not be what they meant.

## Exploratory null analysis

No null distribution for this method appears in the papers listed below. What
follows is a first attempt at one. It should be read as exploratory, for the
reasons given in the Status and Limitations sections.

All p-values are one-sided empirical upper-tail values with the finite-sample
correction `(count(null >= observed) + 1) / (n_resamples + 1)`. With 5,000
draws the floor is 1/5001 = 0.0002, which is the smallest value the design can
express rather than a measurement.

Three randomizations were built:

- **Pool-wide.** Shuffles all notations corpus-wide, obverse and reverse alike.
- **Obverse-only.** Holds every reverse summary exactly as attested and
  permutes whole obverse bundles among tablets with the same number of obverse
  notation slots.
- **Position plus magnitude.** Preserves tablet side and the base-10 order of
  the notation's maximum valid reading.

### Results

| Statistic and control                  | Observed | Null mean | Null std | Null range   | p        |
| -------------------------------------- | -------- | --------- | -------- | ------------ | -------- |
| Subset raw, pool-wide                  | 151      | 147.6738  | 8.2070   | not recorded | 0.370526 |
| Subset raw, obverse-only               | 151      | 63.3836   | 5.1710   | 46-86        | 0.000200 |
| Subset raw, position + magnitude       | 151      | 117.5020  | 6.4662   | 94-138       | 0.000200 |
| Subset witness, obverse-only           | 52       | 12.3854   | 2.7201   | 4-22         | 0.000200 |
| Subset witness, position + magnitude   | 52       | 21.7976   | 3.2497   | 11-35        | 0.000200 |
| Full-sum raw, obverse-only             | 63       | 6.2668    | 2.1863   | 1-15         | 0.000200 |
| Full-sum raw, position + magnitude     | 63       | 5.0912    | 2.1315   | 0-14         | 0.000200 |
| Full-sum witness, obverse-only         | 21       | 0.9378    | 0.9581   | not recorded | 0.000200 |
| Full-sum witness, position + magnitude | 21       | 0.2760    | 0.5210   | not recorded | 0.000200 |

The subset raw p-values under the two sharper controls were read off the
already-computed 5,000-draw sequences by deterministic replay, not from fresh
sampling. The replay reproduces the previously recorded null means and witness
margins exactly.

The full-sum witness null means are close to zero, with many draws at zero, so
ratios against them are unstable and no effect size is reported for those rows.

### What these numbers do and do not support

The same statistic can sit at chance under one null and at the floor of the
scale under another. Subset raw closure is `p = 0.37` against the pool-wide
null and `p = 0.0002` against both sharper ones. **No result here should be
cited without naming its null.**

The pool-wide null is **not an appropriate control** and its row is retained
only because it was run first. It shuffles reverse summaries as well as
obverse entries. Real summaries are large by construction, and a randomly
drawn notation from the pool is typically smaller; small targets are easier to
hit, which inflates the expected closure rate.

Under the sharper controls, observed counts exceed the null for both
definitions. The most that supports is that **some reverse lines are
arithmetically related to the obverse of their own tablet** more than to the
obverse of unrelated tablets of similar shape. That is a statement about the
corpus. It is not a demonstration that the disambiguation method assigns
number systems correctly, and it is not a false-positive rate for the method.

The obverse-only design also assumes that obverse bundles with equal slot
counts are exchangeable. They are not, in several respects: magnitude,
admissible systems, account type, semantic composition, provenance, scribe,
and possible document families. The null breaks all of these at once alongside
the arithmetic relation of interest, so the low p-values partly reflect that
broader destruction rather than the arithmetic relation alone.

## Limitations

- The analyses are exploratory, arrived at sequentially with earlier results
  visible. `NOTES.md` records decision rules before each computation, but this
  is not preregistration.
- Set identity between any count here and the published 24 is unverified.
- The exchangeability assumption behind the obverse-only null is not
  satisfied. A control additionally conditioning on the number of valid
  reverse notations and on summary magnitude profile has not been implemented
  here, and would be expected to raise the null means.
- No claim about corpus change is made on the basis of the reverse-entry
  counts of Appendix A tablets.
- The corpus snapshot is 2023-02-09 and is neither the paper's snapshot nor
  the current CDLI state.
- The work is arithmetic and structural. It does not assign meanings to signs
  or translate a tablet.
- No implicit-object inheritance, bootstrapping classifier, or general
  constraint solver has been implemented.
- No tablet photographs are included. CDLI transliterations and artifact
  images have different reuse conditions.
- The full audit trail, including negative results, corrected conclusions and
  errors, is in [`NOTES.md`](NOTES.md).

## Open questions for the authors

1. Can the 24 P-numbers be shared, so that set identity can be checked rather
   than inferred from counts?
2. What did manual inspection remove, and roughly how many candidates entered
   it?
3. Which corpus snapshot or commit was used, so that the inventory and numeral
   deltas above can be attributed?
4. Is the "unambiguous witness" formalization here a fair reading of the
   evidentiary criterion in section 3.2?
5. Is the P008805 metadata discrepancy below a typo, or a corpus record issue?

## Corpus note

Figure 2 of the corrected paper captions P008805 as "MDP 26, 177," while the
pinned ATF header identifies it as "MDP 26, 117." The displayed
transliteration matches P008805 exactly; the corpus record P008865 carries
"MDP 26, 177" but different content. Recorded for upstream review, not
silently corrected here.

## Repository layout

```
pe/corpus.py       ATF parser with explicit damage and missing-sign states
pe/numerals.py     exact numeral readings across D, S, B, and C
pe/null.py         seeded permutation-test and randomization infrastructure
pe/closure.py      subset-sum and strict full-sum closure checks
tests/             reproduction targets and deterministic sanity checks
data/pe-headers/   pinned corpus submodule
NOTES.md           dated decisions, divergences, and corrections
AGENTS.md          working rules for this repository
```

## Reimplemented work

- Born, L., Kelley, K., Kambhatla, N., Chen, C., and Sarkar, A. 2019. Sign
  Clustering and Topic Extraction in Proto-Elamite. *Proceedings of the 3rd
  Joint SIGHUM Workshop (LaTeCH-CLfL)*, 122-132.
- Born, L., Kelley, K., Monroe, M. W., and Sarkar, A. 2021. Compositionality of
  Complex Graphemes in the Undeciphered Proto-Elamite Script using Image and
  Text Embedding Models. *Findings of ACL-IJCNLP 2021*, 4136-4146.
- Kelley, K., Born, L., Monroe, M. W., and Sarkar, A. 2022. On Newly Proposed
  Proto-Elamite Sign Values. *Iranica Antiqua* 57.
- Born, L., Monroe, M. W., Kelley, K., and Sarkar, A. 2022. Sequence Models for
  Document Structure Identification in an Undeciphered Script. *EMNLP 2022*,
  9111-9121.
- Born, L., Monroe, M. W., Kelley, K., and Sarkar, A. 2023. Disambiguating
  Numeral Sequences to Decipher Ancient Accounting Corpora. *CAWL 2023*, 71-81.
  Corrected revision: [arXiv:2502.00090v2](https://arxiv.org/abs/2502.00090).
- Born, L., Monroe, M. W., Kelley, K., and Sarkar, A. 2023. Learning the
  Character Inventories of Undeciphered Scripts Using Unsupervised Deep
  Clustering. *CAWL 2023*, 92-104.
- Monroe, M. W., Kelley, K., Born, L., and Sarkar, A. 2025. Recent Progress in
  Deciphering Proto-Elamite. *Near Eastern Archaeology* 88.4, 314-323.
- Dahl, J. L. 2019. *Tablettes et fragments proto-élamites / Proto-Elamite
  Tablets and Fragments*. Textes Cunéiformes du Louvre 32.

Corpus data courtesy of the [Cuneiform Digital Library
Initiative](https://cdli.mpiwg-berlin.mpg.de).

## Method note

This repository was built with substantial assistance from AI tools, both for
writing code and for designing the statistical tests. The statistical design
received no independent expert review before publication. An adversarial
review after the first version identified several overclaims, which were
removed rather than softened. The record of what was wrong, and when it was
corrected, is in `NOTES.md`.

## License

Code is released under the MIT License, see [`LICENSE`](LICENSE). Corpus data
in `data/` belongs to its original providers and is governed by CDLI terms of
use.
