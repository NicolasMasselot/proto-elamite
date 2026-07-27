# Session notes

## 2026-07-27 — Session 1: corpus bootstrap

- Attempted: initialized the repository; pinned `sfu-natlang/pe-headers` as
  `data/pe-headers` at `88948d18f3d9c0250c33344fd9e6c8968438869f`
  (2023-02-09); wrote the ATF parser and corpus inventory tests.
- Counts (observed; published; delta): raw texts 1467; 1467; 0. Cleaned texts
  1398; 1399; -1. Entries 11026; 11013; +13. Tokens 33828; 33778; +50.
  Unreadable/missing 7584; 7508; +76. Numerals 11389; 11364; +25.
  Non-numerical tokens 14855; 14906; -51. Non-numerical types 1630; 1623;
  +7. Hapax 744; 745; -1.
- Decided: classify tokens mechanically as identified signs (`M` plus digits),
  identified numerals (quantity plus `(N...)`), or unreadable/missing. Preserve
  raw ATF, `#`, `?`, square-bracket restoration, and `x`; do not infer values.
  A cleaned text has at least one identified non-numerical sign.
- Tests: `uv run pytest -q` passes (6 tests, 0.34 s).
- Divergence: all digit-led ATF entries are parsed. The submodule introduced
  its corpus wholesale in its initial commit, and the papers publish only
  aggregates, so the changed 13 lines/50 tokens cannot be localized against
  this repository's history alone.
- Ruled out: running the authors' pipelines, numeral conversion, arithmetic
  solving, and tuning token rules to recover published totals; all are outside
  this session or would hide the observed delta.
- Next session first: obtain or identify the exact 2019/2021 corpus snapshot
  and diff it tablet-by-tablet against this pin before extending replication.

## 2026-07-27 — Session 2: numeral conversion

- Attempted: transcribed Algorithm 1 and Figure 1 from the corrected arXiv
  revision 2502.00090v2; implemented exact `Fraction` readings for D/S/B/C,
  intact-run extraction, damage filtering, and Table 1 tests.
- Source decision: used the 2025 arXiv revision, not the 2023 proceedings
  version. The proceedings table has the superseded decimal values and reports
  57 invalid readings; the revision reports the target 27 and documents the
  correction.
- Counts (observed; revised paper; delta): intact notations 8008; 8011; -3.
  At least one reading 7959; 7984; -25. Unambiguous 1942; 1899; +43.
  none 49; 27; +22. B 15; 18; -3. C 1743; 1678; +65. D 78; 96; -18.
  S 106; 107; -1. B|D 21; 22; -1. B|S 5; 5; 0. C|D 46; 49; -3.
  C|S 146; 143; +3. B|C|S 177; 185; -8. B|D|S 291; 292; -1.
  All four 5331; 5389; -58.
- Decisions: Figure 1 arrow labels are `max_count` themselves (so `10(N01)`
  is allowed in D/S/B and `11(N01)` is not), matching the revised paper's
  invalid example. Normalize ATF `@` allograph/orientation suffixes and the
  paper's N8A/N8B spelling variants; do not invent readings for signs absent
  from Figure 1. Discard a numeral run when followed by an unreadable/missing
  lower-order token, matching the extraction direction and near-exact 8008
  versus 8011 count.
- Divergence audit: the 49 invalid current notations include N02 in 22,
  N51G in 6, N39A in 4, rarer unlisted signs, explicit over-counts including
  two `11(N01)` notations, and mixed-system digit sequences. No aliases were
  added merely to reduce these deltas.
- Tests: `uv run pytest -q` passes (13 tests, 0.51 s), including Figure 2's
  111.5 N01-S and 44.6 N01-C conversions.
- Ruled out: subset-sum, bootstrapping, constraint solving, contextual
  disambiguation, and tuning Figure 1 values or carry limits.
- Next session first: identify the paper's exact digit-name normalization and
  2022-10-03 corpus snapshot, then diff the 49 invalid notations and the
  C/all-four category movement before accepting either as corpus drift.

### Quick diagnostic before Session 3

- The 49 invalid notations partition as: N02 22, N51G 6, N39A 4, other
  Figure-1-absent signs 7, pure over-counts 6, mixed-system sequences 4.
  All Figure 1 digits occur in `pe-headers`. N02/N51G/N39A also have assets in
  the paper source but are not members of its four system chains; rarer current
  names N14B, N1B, N29B, N39N, N39~b, and N91 have no paper asset.
- The unambiguous +43 is C +65 offset by B/D/S -22. It is not a direct
  carry-constraint transfer from all-four (-58): all-four runs use shared
  N01/N14, and exceeding C's limit turns them into B|D|S, not C-only.
  Instance-level overlap still requires the unavailable paper snapshot.

## 2026-07-27 — Session 3: permutation-test infrastructure

- Attempted: added a generic deterministic upper-tail permutation test and a
  reusable valid-system assignment randomizer; added only synthetic tests.
- Null decision: ambiguous notations draw uniformly from their own valid
  system set. Unambiguous assignments remain fixed and zero-reading items are
  rejected. Sampling all four systems would include readings already ruled
  out by Algorithm 1 and would not test valid-but-unconstrained assignments.
- Seeds: `PERMUTATION_SEED=20260727`; repeated sanity seeds 20260727-20260729.
- No-signal check (observed 10; 2000 draws): null mean/std/p were
  10.1085/2.2673/0.6010, 10.0495/2.1622/0.6000, and
  10.0210/2.2818/0.5885.
- Obvious-signal check (observed 20; 5000 draws): null mean 10.0558, std
  2.2369, p=0.0000 (0 of 5000 draws at least as large).
- Tests: `uv run pytest -q` passes (20 tests, 2.32 s). A repeated seed
  reproduces the entire null distribution.
- Ruled out: arithmetic closure, inheritance, subset-sum, and solver logic.
- Next session first: define the closure statistic and corpus representation,
  then call this null machinery in the same function that reports the result.
- Pre-Session 4 correction: p-values use `(count(null >= observed) + 1) / (n_resamples + 1)`; the prior 0/5000 case is therefore p=1/5001=0.000200, never literal zero.

## 2026-07-27 — Session 4: baseline closure gate (stopped)

- Attempted: implemented only the paper's automatic baseline: retain tablets
  with one or two reverse entries and find a non-empty obverse subset whose
  readings equal a reverse reading in one consistent numeral system.
- Counts: 425 tablets pass the reverse-entry filter; 151 have a raw subset-sum
  closure; 52 closures contain an intrinsically unambiguous notation in the
  actual witness. The paper reports 24 texts retained after manual inspection.
- Known cases: P008014, P008173, and P008012 close. P008179 is excluded in the
  current corpus because it has three reverse entries.
- Decision: 151 (or 52 with the paper's evidentiary condition) versus 24 is a
  substantial baseline divergence. The published 24 include undocumented
  manual inspection and cannot be reproduced as a deterministic automatic
  count from the stated rule. Stopped at the required reproduction gate.
- Tests: `uv run pytest -q` passes for the baseline implementation.
- Not run: implicit-object inheritance, broadened filter, full-corpus extended
  closure, permutation null, and solver. No observed/null mean/null std/p-value
  exists for the extension because proceeding would violate the stop rule.
- Next session first: obtain the authors' 24-tablet list or formalize an
  explicit deterministic replacement for their manual inspection before
  attempting the inheritance extension.

### 2026-07-27 correction after the strict full-sum check

- The reported 52-versus-24 divergence was an artifact of using the
  permissive subset definition. Under the strict definition in which every
  obverse notation participates, 21 candidates close with an unambiguous
  witness versus the published 24 (delta -3). The earlier hypothesis that
  undocumented manual inspection was needed to explain the numerical gap is
  therefore withdrawn; manual inspection may still be part of the paper's
  procedure, but it is not needed to account for 21 versus 24.

## 2026-07-27 — Session 4b: baseline closure null

- Attempted: added a notation-pool shuffle for the existential baseline
  statistic, preserving all 425 tablets, their obverse/reverse entry counts,
  and their notation-slot counts. Each draw samples without replacement from
  the corpus-wide pool of 7959 valid notations and retains every notation's
  full valid reading set before rerunning existential closure. The older
  valid-system assignment randomizer remains available but is not the right
  null for an existential search because it fixes one reading per notation.
- Raw closure: observed 151/425 (35.5294%); 5000-draw null mean 147.6738
  (34.7468%), std 8.2070 (1.9311 percentage points), upper-tail
  p=0.370526. Raw baseline closure does not exceed this null, so the arithmetic
  closure exit condition is not cleared.
- With-unambiguous-witness closure: observed 52/425 (12.2353%); null mean
  11.8380 (2.7854%), std 3.0532 (0.7184 percentage points), p=1/5001
  (0.000200; zero of 5000 draws reached 52).
- Replication finding on the published 24: it is a post-manual-inspection
  count, while the pre-inspection count is unpublished. The closest
  deterministic analogue to the stated rule yields 52 with an unambiguous
  witness. P008179 is excluded because the current transcription has three
  reverse entries rather than the one-or-two-entry filter required by the
  paper.
- Decisions: used `PERMUTATION_SEED=20260727`, the corrected add-one p-value,
  and the pre-specified 5000 resamples. No tuning followed either result.
  Implemented no implicit-object inheritance and stopped at the exit
  condition.
- Tests: the encoded baseline reproduces 425 candidates, 7959 pool
  notations, 2642 candidate slots, and the 151/52 observed scores; the null
  tests also lock in shape preservation and retained valid reading sets.
- Next session first: write up the negative raw-closure result; do not resume
  inheritance without a new reason that changes the project exit condition.

## 2026-07-27 — Session 5: witness-signal diagnosis

- Decision rule, recorded before computing the new marginals or permutation
  results: if the unambiguous-witness statistic has `p > 0.01` under either
  the position-stratified null or the notation-length-stratified null, judge
  the witness signal compositional rather than arithmetic, write that up as
  the finding, and stop this line of work. Do not revise this threshold after
  observing the results.
- Marginal check: across the full corpus, reverse notations are 380/1131
  unambiguous (33.5986%), obverse notations 1561/6718 (23.2361%), and the
  overall pool 1942/7959 (24.4001%). In the 425 closure candidates the
  contrast is larger: reverse 200/424 (47.1698%), obverse 495/2218
  (22.3174%), and all candidate slots 695/2642 (26.3058%).
- The original pool-wide null erases that margin. Across its 5000 fixed-seed
  draws, mean unambiguous fractions are 24.4108% in reverse slots, 24.4020%
  in obverse slots, and 24.4034% across all drawn slots. The positional
  confound is therefore present in the unstratified design.
- Position-stratified witness closure (5000 draws): observed 52; null mean
  11.6702; null std 2.9952; p=1/5001 (0.000200; null range 1--23, with zero
  draws reaching 52). Reverse slots draw only from the 1131 full-corpus
  reverse notations and obverse slots only from the 6718 obverse notations.
- Distinct-digit-sign-length-stratified witness closure (5000 draws):
  observed 52; null mean 10.0936; null std 2.9045; p=1/5001 (0.000200; null
  range 1--22, with zero draws reaching 52). Every slot retains its original
  notation-length stratum while the full valid-reading set travels with the
  sampled notation.
- Comparison: the unstratified result was observed 52, null mean 11.8380,
  null std 3.0532, p=1/5001. Neither stratified p-value exceeds the
  preregistered 0.01 cutoff, so this rule does not classify the witness
  excess as compositional. Position and distinct-digit-sign length do not
  explain it under these controls.
- Decision: retain the Session 4b negative result that raw closure itself is
  at chance (151 observed versus null mean 147.6738, p=0.370526). The
  surviving witness-conditioned excess does not reverse that arithmetic
  closure exit condition, so no inheritance work was started.
- Tests: added deterministic checks that stratified draws preserve tablet
  shape, position pools, individual notation-length strata, full valid
  reading sets, and the observed corpus composition margins.
- Next session first: write up the distinction between chance-level raw
  closure and the surviving witness-conditioned association; do not present
  the latter as evidence that closure per se exceeds chance.

## 2026-07-27 — Session 6: obverse-only control

- Decision rule, recorded before computing the Session 6 P-number set,
  conditional rates, or permutation results: if the obverse-only shuffle
  gives `p > 0.01`, judge the witness excess an artifact of magnitude or
  tablet-size compatibility and close this line with a negative writeup. If
  `p <= 0.01`, testing stops and the result is written up as it stands; run
  no further nulls. The requested position-plus-magnitude control will run
  regardless because it is a secondary control, not the gate. Do not revise
  this rule after observing either result.
- Obverse-only control (5000 draws): held every reverse notation fixed and
  permuted whole obverse bundles only among tablets with equal obverse
  notation-slot counts. Observed witness closures 52; null mean 12.3854;
  null std 2.7201; p=1/5001 (0.000200; null range 4--22, zero draws reached
  52). The gate is `p <= 0.01`, so testing stops after the already-specified
  secondary control and no further null is permitted for this result.
- Position-plus-magnitude control (5000 draws): stratified notation pools by
  surface and by the base-10 order of the maximum valid reading in N01 units.
  Observed 52; null mean 21.7976; null std 3.2497; p=1/5001 (0.000200; null
  range 11--35, zero draws reached 52).
- Conditional effect: observed witness/all closure is 52/151 = 34.4371%.
  Under the obverse-only null, mean counts are 12.3854/63.3836 and the mean
  paired draw-wise rate is 19.5199% (ratio of means 19.5404%). Under the
  position-plus-magnitude null, mean counts are 21.7976/117.5020 and the mean
  paired rate is 18.5553% (ratio of means 18.5508%).
- The 52 witness-conditioned tablets are: P008014, P008016, P008018,
  P008019, P008020, P008069, P008106, P008140, P008150, P008169, P008173,
  P008215, P008243, P008275, P008292, P008308, P008313, P008387, P008419,
  P008426, P008438, P008626, P008641, P008709, P008753, P008783, P008821,
  P008844, P008946, P008984, P008998, P009001, P009011, P009014, P009028,
  P009041, P009092, P009155, P009166, P009193, P009196, P009207, P009219,
  P009239, P009366, P009432, P009441, P009444, P009524, P009525, P009526,
  P009531.
- Appendix A validation: 3/15 cited tablets occur in the 52 (P008014,
  P008173, P008243); 12/15 do not; none are absent from the corpus. P008791,
  P008797, P008798, P008799, P008800, P008801, P008802, P008804, and
  P008810 have zero reverse entries in the current transcription and fail
  the baseline filter. P008179 has three reverse entries and P009048 has
  four, so both also fail the filter. P008012 is a baseline candidate and
  closes raw, but has no unambiguous witness and therefore is not in the 52.
- Decisions: the witness-conditioned excess survives the sharp obverse-only
  control and the secondary magnitude control under the fixed rule. Preserve
  separately the negative raw-closure finding (`p=0.370526`); the conditional
  result does not turn raw closure into an above-null result. No inheritance
  logic was implemented and no parameter was changed after either p-value.
- Tests: lock the obverse-bundle invariants, exact magnitude buckets, paired
  151/52 closure counts, all 52 P-numbers, and the 3-tablet Appendix A
  overlap.
- Next session first: write up the witness-conditioned result and its
  chance-level raw-closure limitation. Do not run another null for this
  result.

### Final definitional check: subset versus full sum

- Reporting commitment, recorded before computing any full-sum count,
  permutation result, or P008805 diagnostic: the writeup will report the
  subset-sum and strict full-sum definitions side by side, regardless of
  which produces the lower p-value. We will not select between definitions
  after observing their results. Only the requested obverse-only and
  position-plus-magnitude 5000-draw controls will be run for the full-sum
  witness statistic; no further null follows them.
- Definition: strict full sum requires every encoded valid obverse numeral
  notation to have a reading in one common system and the sum of all of them
  to equal one attested reverse reading. It never selects a proper subset.
- Observed counts across the same 425 candidates: subset sum closes 151,
  including 52 with an unambiguous witness; full sum closes 63, including 21
  with an unambiguous witness. Conditional witness/all rates are respectively
  52/151 = 34.4371% and 21/63 = 33.3333%.
- Obverse-only control, subset versus full sum: subset witness observed 52,
  null mean 12.3854, std 2.7201, p=1/5001; full-sum witness observed 21, null
  mean 0.9378, std 0.9581, p=1/5001. The subset paired-null conditional rate
  is 19.5199% (mean counts 12.3854/63.3836); the full-sum rate is 14.3864%
  (mean counts 0.9378/6.2668).
- Position-plus-magnitude control, subset versus full sum: subset witness
  observed 52, null mean 21.7976, std 3.2497, p=1/5001; full-sum witness
  observed 21, null mean 0.2760, std 0.5210, p=1/5001. The subset paired-null
  conditional rate is 18.5553% (mean counts 21.7976/117.5020); the full-sum
  rate is 5.3029% over the 4978 draws with a defined denominator (mean counts
  0.2760/5.0912; 22 draws have zero raw closures).
- Raw full-sum p-values were extracted from those existing 5000-draw sets,
  not from new sampling. For the obverse-only draws, raw closure is 63
  observed versus null mean 6.2668, std 2.1863, range 1--15, with
  p=1/5001. For the position-plus-magnitude draws, it is 63 versus null mean
  5.0912, std 2.1315, range 0--14, also p=1/5001. Deterministically replaying
  the fixed seed reproduced the previously recorded means and standard
  deviations exactly and was used only to read the raw upper-tail counts
  from the same pseudo-random sequences; no seed, draw count, or null was
  added.
- P008805 sanity check: the parser returns exactly two entries, both obverse,
  with numeral notations `1(N34) 5(N14) 1(N01) 1(N8B)` and
  `7(N14) 2(N01) 3(N39B)`, matching the two transliteration rows visible in
  the paper's Figure 2. The ATF then opens a reverse surface containing only
  a blank-space marker, so zero reverse entries is correct and the
  425-candidate filter does not need revision. The paper caption calls the
  object MDP 26, 177 while the current P008805 ATF header says MDP 26, 117;
  the displayed transliteration nevertheless identifies P008805 exactly and
  this metadata discrepancy does not affect surface assignment.
- Decision: report both definitions. Both full-sum controls were the only
  additional nulls run, and no more will follow. No inheritance logic was
  implemented.
- Tests: lock the strict all-obverse behavior, observed full-sum 63/21
  counts, and P008805's two obverse-only Figure 2 notations.

### 2026-07-27 corpus note for upstream

- Figure 2 of the revised CAWL paper captions P008805 as MDP 26, 177, while
  the pinned current ATF header identifies P008805 as MDP 26, 117. The
  figure's two transliteration rows match P008805 exactly; P008865 is the
  current corpus record headed MDP 26, 177 and has different content. This
  catalog-number discrepancy is worth reporting upstream to the paper
  authors and CDLI. Do not silently alter the pinned corpus.

## 2026-07-27 — Public README

- Attempted: added a public-facing README with a reproducible `uv` setup,
  pinned-submodule instructions, the corpus and numeral replication tables,
  subset and full-sum closure definitions, all pre-registered null results,
  interpretation limits, and the P008805 metadata note.
- Decision: lead with measured outcomes and deltas; describe this as a
  deterministic replication and arithmetic-constraint project, never as a
  decipherment. Preserve the chance-level subset result beside the stricter
  full-sum controls.
- Ruled out: adding a new analysis, rerunning a null, claiming sign meanings,
  or implying that corpus images are redistributable.
- Next session first: keep README figures synchronized with tests and
  `NOTES.md` whenever a result changes.
