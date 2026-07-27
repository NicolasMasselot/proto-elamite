# Proto-Elamite arithmetic replication

An independent, deterministic replication of published computational results
on the proto-Elamite corpus, followed by narrowly scoped tests of arithmetic
closure.

This is **not a decipherment project**. It does not ask a model to interpret
signs, guess meanings, or translate texts. Parsing, numeral conversion,
constraint checks, and permutation tests are ordinary seeded Python code.

## Reproduce it

Requirements:

- Python 3.11 or later
- [`uv`](https://docs.astral.sh/uv/)
- Git with submodule support

```bash
git clone --recurse-submodules https://github.com/NicolasMasselot/proto-elamite.git
cd proto-elamite
uv sync
uv run pytest -q
```

The test suite currently contains 34 tests and runs in under a minute on a
laptop. It requires no GPU, API key, or network access after the repository
and submodule have been cloned.

The canonical corpus is
[`sfu-natlang/pe-headers`](https://github.com/sfu-natlang/pe-headers), pinned
as a submodule at:

```text
88948d18f3d9c0250c33344fd9e6c8968438869f
```

That snapshot is dated 2023-02-09. Every random process uses the fixed seed
`20260727`.

## Current results

The purpose of the replication is to report movement against the published
figures, not to adjust the implementation until they match.

### Corpus inventory

| Figure | Published | This snapshot | Delta |
|---|---:|---:|---:|
| Raw texts | 1,467 | 1,467 | 0 |
| Cleaned texts | 1,399 | 1,398 | -1 |
| Entries | 11,013 | 11,026 | +13 |
| Tokens | 33,778 | 33,828 | +50 |
| Broken or unreadable | 7,508 | 7,584 | +76 |
| Numerals | 11,364 | 11,389 | +25 |
| Non-numerical tokens | 14,906 | 14,855 | -51 |
| Non-numerical types | 1,623 | 1,630 | +7 |
| Hapax non-numerical types | 745 | 744 | -1 |

Damage is retained rather than discarded. The parser distinguishes an
identified but broken sign, an unreadable sign, and a missing sign.

### Numeral conversion

Numerals are converted under the decimal (D), sexagesimal (S),
bisexagesimal (B), and capacity (C) systems using Algorithm 1 and Figure 1
from the corrected revision of Born et al.,
[arXiv:2502.00090v2](https://arxiv.org/abs/2502.00090).

| Valid systems | Published | This snapshot | Delta |
|---|---:|---:|---:|
| None | 27 | 49 | +22 |
| B | 18 | 15 | -3 |
| C | 1,678 | 1,743 | +65 |
| D | 96 | 78 | -18 |
| S | 107 | 106 | -1 |
| B \| D | 22 | 21 | -1 |
| B \| S | 5 | 5 | 0 |
| C \| D | 49 | 46 | -3 |
| C \| S | 143 | 146 | +3 |
| B \| C \| S | 185 | 177 | -8 |
| B \| D \| S | 292 | 291 | -1 |
| B \| C \| D \| S | 5,389 | 5,331 | -58 |

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
|---|---:|---:|---:|
| Subset sum | 151 | 52 | 34.4371% |
| Full sum | 63 | 21 | 33.3333% |

The paper reports 24 texts after manual inspection. The strict full-sum
witness count is the closest automatic analogue here: 21 (`delta -3`). The
earlier 52-versus-24 gap was an artifact of using the subset definition.

#### Null results

All p-values are one-sided empirical upper-tail values with the finite-sample
correction:

```text
(count(null >= observed) + 1) / (n_resamples + 1)
```

Each reported control uses 5,000 draws.

| Definition and control | Witness observed | Witness null mean | Null std | p | Observed conditional rate | Null conditional rate |
|---|---:|---:|---:|---:|---:|---:|
| Subset, obverse-only | 52 | 12.3854 | 2.7201 | 0.000200 | 34.4371% | 19.5199% |
| Subset, position + magnitude | 52 | 21.7976 | 3.2497 | 0.000200 | 34.4371% | 18.5553% |
| Full, obverse-only | 21 | 0.9378 | 0.9581 | 0.000200 | 33.3333% | 14.3864% |
| Full, position + magnitude | 21 | 0.2760 | 0.5210 | 0.000200 | 33.3333% | 5.3029% |

The obverse-only control keeps every reverse summary exactly as attested and
permutes whole obverse bundles only among tablets with the same number of
obverse notation slots. The position-plus-magnitude control preserves the
tablet side and the base-10 order of the notation's maximum valid reading.

For the full-sum raw statistic:

| Control | Raw observed | Raw null mean | Null std | Null range | p |
|---|---:|---:|---:|---:|---:|
| Obverse-only | 63 | 6.2668 | 2.1863 | 1-15 | 0.000200 |
| Position + magnitude | 63 | 5.0912 | 2.1315 | 0-14 | 0.000200 |

For comparison, permissive subset closure under the earlier unstratified
pool-wide null sits at chance: 151 observed, null mean 147.6738, null standard
deviation 8.2070, `p = 0.370526`. That result and the stricter controls are
both retained; no definition or null was selected after observing its
p-value.

## Repository layout

```text
pe/corpus.py       ATF parser with explicit damage and missing-sign states
pe/numerals.py     exact numeral readings across D, S, B, and C
pe/null.py         seeded permutation-test and randomization infrastructure
pe/closure.py      subset-sum and strict full-sum closure checks
tests/             reproduction targets and deterministic sanity checks
data/pe-headers/   pinned corpus submodule
NOTES.md           dated decisions, divergences, and preregistrations
```

## Interpretation limits

- The pinned corpus postdates the paper's documented 2022-10-03 download, so
  corpus drift is a plausible source of some deltas.
- The result is arithmetic and structural. It does not assign meanings to
  signs or translate a tablet.
- No implicit-object inheritance, bootstrapping classifier, or general
  constraint solver has been implemented.
- No tablet photographs are included. CDLI transliterations and artifact
  images have different reuse conditions.
- The complete audit trail, including negative results and preregistered stop
  rules, is in [`NOTES.md`](NOTES.md).

## Corpus note

Figure 2 of the corrected paper captions P008805 as “MDP 26, 177,” while the
pinned ATF header identifies it as “MDP 26, 117.” The displayed
transliteration matches P008805 exactly; the current corpus record P008865
carries “MDP 26, 177” but different content. This metadata discrepancy is
recorded for upstream review and is not silently corrected here.

