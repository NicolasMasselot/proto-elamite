"""Pinned inputs used by every deterministic result."""

from pathlib import Path

CORPUS_COMMIT = "88948d18f3d9c0250c33344fd9e6c8968438869f"
CORPUS_COMMIT_DATE = "2023-02-09"
CORPUS_DIR = (
    Path(__file__).resolve().parents[1] / "data" / "pe-headers" / "corpus"
)

# Random processes take an explicit seed; these constants pin reported runs.
PERMUTATION_SEED = 20260727
NULL_SANITY_CHECK_SEEDS = (20260727, 20260728, 20260729)

