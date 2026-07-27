# Proto-Elamite: reproducibility and arithmetic constraints

## What this project is

An independent replication and extension of the computational work on the
undeciphered proto-Elamite (PE) script by Born, Kelley, Monroe and Sarkar
(2019-2025). Two deliverables, in order:

1. **Replication.** Recompute the published quantitative claims against the
   current CDLI snapshot and report which ones move. Nobody has done this,
   and the authors themselves note the signlist keeps changing.
2. **Extension.** Systematically resolve implicit counted objects across
   entries using arithmetic constraints. The authors flag this as necessary
   ("there exist long-distance dependencies between the entries in some texts,
   which need to be accounted for if these texts are to be fully understood",
   Born et al. 2023) and never return to it.

The output is a repository a stranger clones and runs in under a minute to
verify every claim, without trusting the author and without domain expertise.

## What this project is not

Not a decipherment. Not an attempt to read proto-Elamite. Not an application
of large language models to an undeciphered script. Any drift in that
direction is a failure, not a pivot.

## The three-layer rule

This is the single hardest constraint in the project.

**Layer 0, deterministic.** Parsing, counting, constraint solving, permutation
testing. **Every published result lives here.** Exhaustive, reproducible,
seeded, no network calls, no model calls.

**Layer 1, model writes the code.** Claude Code writes and debugs Layer 0.
Normal software engineering.

**Layer 2, model generates hypotheses.** Permitted only where Layer 0 can
verify the output exhaustively and for free. Currently the only sanctioned
use is sign-image alignment in the vision spike, which has ground truth from
the CDLI transliteration.

**If a result depends on a model's judgement, it is not a result.** When in
doubt about which layer something belongs in, it belongs in Layer 0 or it
does not go in the repository.

## Falsifiability rules

- Every positive finding ships with a permutation test in the same function
  that produces it. Not in an appendix, not later. The null machinery is
  built before the first result, not after.
- Report the effect size, the null distribution, and the p-value together or
  report nothing.
- Negative results are deliverables. "The arithmetic closure with object
  inheritance does not exceed chance" is a publishable, useful outcome and
  must be written up with the same care as a positive one.
- Never describe a number as significant, striking, promising or interesting
  in code comments, commit messages or output. State the number and the null.

## Reproduction targets

These are the published figures. The replication succeeds when each is
recomputed and the delta is reported, whatever the delta is.

Born et al. 2019 (LaTeCH), cleaned corpus:
- 1399 texts after removing tablets bearing only unreadable or numeric signs
- mean 27 readable signs per text, of which ~10 non-numeric
- longest text: 724 readable signs, 198 non-numeric
- signlist: 49 numeric, 1623 non-numeric signs
- of the non-numeric: 287 basic, 1087 variants, 249 complex graphemes
- 745 of 1623 signs are hapax
- top unigrams: M288 (829), M388 (620), M218 (525), M371 (308), M124 (294),
  M297 (265), M054 (258), M346 (249), M387 (249), M066 (243)
- top bigram: M004 M218 (45)
- most frequent trigram: M377~e M347 M371 (17)
- 11 trigrams repeated 5+ times; 52 repeated 3-4 times; ~98% appear once or twice
- no 4-gram or 5-gram appears more than 3 times; no 6-gram more than twice;
  no 7-gram more than once

Born et al. 2021 (Findings ACL):
- 11013 lines, 33778 tokens total
- 7508 broken or unreadable, 11364 numerals, 14906 non-numerical
- 1107 tokens labeled as complex graphemes

Born et al. 2022 (EMNLP), headers:
- ~26k readable tokens across 1467 transliterated texts
- 795 documents survive pruning for intact beginnings
- of those, 615 annotated with a header, 180 without
- 5 human-labeled two-sign headers
- HMM state 7 begins 55% of texts; precision 0.93, recall 0.67, accuracy 0.70
- logistic regression on Transformer attention: 92%, rising to 95% and
  kappa 0.849 after correcting 25 annotations

Born et al. 2023 (CAWL), numerals:
- 8011 intact numerals extracted; 7984 with at least one valid reading
- 1899 unambiguous; 27 with no valid reading in any system
- reading distribution: B 18, C 1678, D 96, S 107, B|D 22, B|S 5, C|D 49,
  C|S 143, B|C|S 185, B|D|S 292, all four systems 5389
- tablets unambiguously mixing systems: C+S 12, C+D 15, C+B 4, S+D 1
- of 244 signs preceding at least two unambiguous notations, 11 span distinct
  systems: M001, M056~f, M059, M096, M124, M218, M305, M327, M371, M387, M388
- subset-sum analysis disambiguates 24 texts
- bootstrap F1: 0.88 baseline vs 0.94 theirs (4-way); 0.90 vs 0.96 (2-way)
- test set is 48 items only: B 3, C 18, D 14, S 13

Born et al. 2023 (CAWL), character inventories:
- ~1581 tablets, working signlist ~1500 signs, 35k tokens, 1319 sign images
- sign counts range 287 to 1623 depending on counting methodology

If a recomputed figure diverges, that divergence is the finding. Do not tune
the pipeline until it matches. Investigate why, document it, move on.

## Data sources

Canonical corpus: `sfu-natlang/pe-headers`. It contains the transliterations
with expert corrections applied, plus a CSV of labels and model predictions.
Use this as the base unless there is a documented reason not to.

Other repositories, in rough order of usefulness:
- `sfu-natlang/pe-sign-value-data` (full corpus remapped with Desset values)
- `sfu-natlang/pe-decipher-toolkit` (2019 snapshot and exploration tools)
- `sfu-natlang/pe-compositionality` (2021 code, data, trained models)
- `MrLogarithm/pe-pc-datasets-interface` (PE and proto-cuneiform sign counts)
- `MrLogarithm/cawl-clustering` (2023 VAE clustering code)
- `cdli-gh/data` (daily ATF dump, needs git-lfs)
- `cdli-gh/proto-elamite_data` (sign images, EPS)

Prior art to check before duplicating: `MahmoodKhalil57/ProtoElamite`.

Live corpus: CDLI at cdli.mpiwg-berlin.mpg.de. Transliterations are freely
reusable with attribution. **Artifact images are not**: they follow separate
CDLI terms and rights often sit with the holding museum, mostly the Louvre.
Never commit tablet photographs to this repository.

Pin the snapshot date in a constant. Record it in every output.

## Do not run their code

The goal is to recompute their numbers, not to re-execute their pipelines.
The 2019 descriptive statistics are recoverable in a few dozen lines from raw
ATF. Reaching for their 2019-2021 Python is a dependency archaeology trap that
can cost weeks. Only go there if a specific divergence cannot be explained
any other way, and timebox it.

## Code conventions

- Python. One package, flat. No framework, no orchestration layer, no agent
  architecture. The corpus is 1400 texts; a module and a notebook beat
  anything clever.
- `uv` for environment and dependencies.
- OR-Tools CP-SAT for the constraint solver. Instances are tiny (under ~30
  entries per tablet), so brute force the simple version first and only
  reach for the solver when the search space actually demands it.
- Every random process takes an explicit seed. Seeds live in one constants
  module.
- Any network fetch is cached to disk on first call, keyed by hash. There is
  no second uncached fetch, ever.
- No LLM call inside a loop. If one seems necessary, stop and ask why
  Layer 0 is not doing the work.
- `pytest` for anything with a known answer, including the reproduction
  targets above. The replication table should be a test suite.
- `verify.py` at the root prints the full claim table and exits 0. It must
  run in under 60 seconds on a laptop with no GPU and no API key.

## Session protocol

This project runs on weekends over several months. Every session starts cold,
sometimes weeks after the last one. That discontinuity, not time pressure, is
the main risk.

At the start of every session, read `NOTES.md` before anything else.

At the end of every session, append to `NOTES.md`:
- what was attempted
- what the numbers were
- what was decided and why
- what the next session should do first
- anything that was ruled out, with the reason

Keep entries short and dated. This file is the project's actual memory. It
matters more than the code.

Scope each session to fit a single sitting of a few hours. If a task cannot
be finished in one sitting, split it before starting.

## Exit conditions

Check these honestly. Unlimited time is how projects rot, not how they succeed.

- **Replication.** If the recomputed 2019 descriptives do not land within a
  few percent of the published figures, stop extending and find out why. That
  investigation is the replication result.
- **Arithmetic closure.** If the count of arithmetically closed tablets does
  not exceed the permutation null, stop, write the negative result, ship it.
  Do not add heuristics until it works. A closure that only appears after
  three rounds of tuning is a tuning artifact.
- **Vision spike.** If sign-image alignment against the known transliteration
  sequence is no better than chance on a 30-image sample, the segmentation
  branch is closed. Record the numbers and do not revisit without a new reason.

## Explicit prohibitions

- Do not ask a model to interpret, translate or guess the meaning of a
  proto-Elamite sign, sequence or tablet. Its training data on this script is
  the same seven papers already read. It will produce fluent, confident,
  worthless output.
- Do not build a skill, plugin or pipeline abstraction for this project.
- Do not rent a GPU. Everything here fits on a laptop; the 2022 team trained
  their Transformer in about an hour on a GTX 1070.
- Do not commit tablet images.
- Do not write interpretive claims about what a sign means. That requires
  expertise this project does not have and does not need.
- Do not describe this work as a decipherment, a breakthrough, or an
  AI-assisted advance, in the repository or anywhere else.
