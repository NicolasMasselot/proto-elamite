# Proto-Elamite arithmetic replication

An independent, deterministic replication of published computational results
on the proto-Elamite corpus, followed by narrowly scoped tests of arithmetic
closure.

This is **not a decipherment project**. It does not ask a model to interpret
signs, guess meanings, or translate texts. Parsing, numeral conversion,
constraint checks, and permutation tests are ordinary seeded Python code.

## Result

- **The closure method works.** Under the strict full-sum definition, 63 of
  425 candidate tablets close arithmetically, against a null mean of 6.27
  (obverse-only control, 5,000 draws, `p = 0.0002`). No null distribution for
  this method appears in the published literature, so this is the first
  quantitative evidence that the method detects something other than
  combinatorial coincidence.
- **The published count replicates.** Full-sum closure with an unambiguous
  witness yields 21 tablets against the 24 reported by Born et al. (2023).
- **A permissive definition destroys the signal.** Allowing any obverse subset
  rather than the full sum raises the raw count from 63 to 151, while dropping
  it to chance level under a pool-wide null. Same corpus, same machinery, one
  definitional choice.
- **Corpus drift is measurable.** Nine tablets cited in the paper's Appendix A
  now have zero reverse entries in the current transcription, and two others
  have three and four.

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

The canonical corpus is [`sfu-natlang/pe-headers`](https://github.com/sfu-natlang/pe-headers), pinned
as a submodule at:

```
88948d18f3d9c0250c33344fd9e6c8968438869f
```

That snapshot is dated 2023-02-09. Every random process uses the fixed seed
`20260727`.

## Detailed results

The purpose of the replication is to report movement against the published
figures, not to adjust the implementation until they match.

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
from the corrected revision of Born et al., [arXiv:2502.00090v2](https://arxiv.org/abs/2502.00090).

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

The 49 invalid notations are documented rather than normalized away. Their
causes include Figure-1-absent signs, over-counts before carrying, and
mixed-system sequences.

### Arithmetic closure

The baseline candidate set contains 425 tablets with one or two reverse
entries. Two definitions are reported side by side:

- **Subset sum:** any non-empty subset of obverse numeral readings may equal a
  reverse reading.
- **Full sum:** every valid obverse numeral notation must participate under
  one consistent system.

| Definition | Raw closures | With an unambiguous witness | Witness / raw |
| ---------- | ------------ | --------------------------- | ------------- |
| Subset sum | 151          | 52                          | 34.4371%      |
| Full sum   | 63           | 21                          | 33.3333%      |

The paper reports 24 texts after manual inspection. The strict full-sum
witness count is the closest automatic analogue here: 21 (`delta -3`). The
earlier 52-versus-24 gap was an artifact of using the subset definition, and
undocumented manual filtering is not needed to explain it.

**Set identity is unverified.** The counts are close, but the paper does not
publish its 24 P-numbers, so the two sets cannot be compared directly. Of the
15 tablets cited in the paper's Appendix A, 3 appear in the subset-sum witness
set here (P008014, P008173, P008243). Most of the remainder were disambiguated
in the paper by evidence other than subset-sum, chiefly the 2.5:1 ratio of
M056~f to M288, so their absence is expected rather than a failed check.
Two counts of close-but-not-identical size are not proof of the same result.

#### Null results

All p-values are one-sided empirical upper-tail values with the finite-sample
correction:

```
(count(null >= observed) + 1) / (n_resamples + 1)
```

Each reported control uses 5,000 draws.

| Definition and control       | Witness observed | Witness null mean | Null std | p        | Observed conditional rate | Null conditional rate |
| ---------------------------- | ---------------- | ----------------- | -------- | -------- | ------------------------- | --------------------- |
| Subset, obverse-only         | 52               | 12.3854           | 2.7201   | 0.000200 | 34.4371%                  | 19.5199%              |
| Subset, position + magnitude | 52               | 21.7976           | 3.2497   | 0.000200 | 34.4371%                  | 18.5553%              |
| Full, obverse-only           | 21               | 0.9378            | 0.9581   | 0.000200 | 33.3333%                  | 14.3864%              |
| Full, position + magnitude   | 21               | 0.2760            | 0.5210   | 0.000200 | 33.3333%                  | 5.3029%               |

The obverse-only control keeps every reverse summary exactly as attested and
permutes whole obverse bundles only among tablets with the same number of
obverse notation slots. The position-plus-magnitude control preserves the
tablet side and the base-10 order of the notation's maximum valid reading.

Two caveats on the full-sum rows. The null means are close to zero, so ratios
against them are unstable and are not reported as effect sizes; the raw
statistic below has a better behaved denominator. The 5.3029% figure is
computed over the 4,978 draws with a defined denominator, since 22 draws
produce zero raw closures.

For the full-sum raw statistic:

| Control              | Raw observed | Raw null mean | Null std | Null range | p        |
| -------------------- | ------------ | ------------- | -------- | ---------- | -------- |
| Obverse-only         | 63           | 6.2668        | 2.1863   | 1-15       | 0.000200 |
| Position + magnitude | 63           | 5.0912        | 2.1315   | 0-14       | 0.000200 |

#### On the pool-wide null

Permissive subset closure under an earlier unstratified pool-wide null sits at
chance: 151 observed, null mean 147.6738, null standard deviation 8.2070,
`p = 0.370526`.

That null is retained here because it was run first and because the contrast
is instructive, but it is not the appropriate control. It shuffled reverse
summaries as well as obverse entries. Real summaries are large by
construction, and a randomly drawn notation from the corpus pool is typically
smaller; small targets are easier to hit with a subset, which inflated the
expected closure rate and made the real corpus look unremarkable. The
obverse-only control holds each real summary fixed and removes this confound.

No definition or null was selected after observing its p-value. Decision rules
were recorded in `NOTES.md` before each statistic was computed.

## Repository layout

```
pe/corpus.py       ATF parser with explicit damage and missing-sign states
pe/numerals.py     exact numeral readings across D, S, B, and C
pe/null.py         seeded permutation-test and randomization infrastructure
pe/closure.py      subset-sum and strict full-sum closure checks
tests/             reproduction targets and deterministic sanity checks
data/pe-headers/   pinned corpus submodule
NOTES.md           dated decisions, divergences, and preregistrations
AGENTS.md          working rules for this repository
```

## Interpretation limits

- The pinned corpus postdates the paper's documented 2022-10-03 download, so
  corpus drift is a plausible source of some deltas.
- The result is arithmetic and structural. It does not assign meanings to
  signs or translate a tablet.
- The full-sum witness count and the published count are close, but the two
  sets have not been shown to coincide.
- No implicit-object inheritance, bootstrapping classifier, or general
  constraint solver has been implemented.
- No tablet photographs are included. CDLI transliterations and artifact
  images have different reuse conditions.
- The complete audit trail, including negative results and preregistered stop
  rules, is in [`NOTES.md`](NOTES.md).

## Corpus note

Figure 2 of the corrected paper captions P008805 as "MDP 26, 177," while the
pinned ATF header identifies it as "MDP 26, 117." The displayed
transliteration matches P008805 exactly; the current corpus record P008865
carries "MDP 26, 177" but different content. This metadata discrepancy is
recorded for upstream review and is not silently corrected here.

## Replicated work

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

## License

Code is released under the MIT License, see [`LICENSE`](LICENSE). Corpus data
in `data/` belongs to its original providers and is governed by CDLI terms of
use.
