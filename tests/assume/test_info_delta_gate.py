"""tests/assume/test_info_delta_gate.py — S5 정보델타 발권 트리거(rate-cap AND 델타)."""
import numpy as np
import pytest

from core.assume.info_delta_gate import RateCapState, cosine_novelty, delta_gate


@pytest.fixture
def rng():
    return np.random.RandomState(1)


@pytest.fixture
def corpus(rng):
    return [rng.randn(32) for _ in range(5)]


def test_novel_info_fires(rng, corpus):
    d = delta_gate(rng.randn(32), corpus, novelty_min=0.15)
    assert d.fire and d.novelty > 0.15


def test_duplicate_info_skips(rng, corpus):
    dup = corpus[0] + rng.randn(32) * 1e-3
    d = delta_gate(dup, corpus, novelty_min=0.15)
    assert not d.fire and "무의미" in d.reason


def test_numeric_revision_fires_despite_low_novelty(rng, corpus):
    dup = corpus[0] + rng.randn(32) * 1e-3
    d = delta_gate(dup, corpus, novelty_min=0.15, numeric_revision=-0.25, numeric_revision_min=0.05)
    assert d.fire and "수치리비전" in d.reason


def test_rate_cap_blocks_burst(rng, corpus):
    rc = RateCapState(cap_per_slot=2, slot_fn=lambda t: int(t) // 10)
    fires = [delta_gate(rng.randn(32), corpus, rate_cap=rc, tick=3).fire for _ in range(4)]
    assert fires == [True, True, False, False]


def test_next_slot_resets_counter(rng, corpus):
    rc = RateCapState(cap_per_slot=2, slot_fn=lambda t: int(t) // 10)
    for _ in range(2):
        delta_gate(rng.randn(32), corpus, rate_cap=rc, tick=3)
    assert delta_gate(rng.randn(32), corpus, rate_cap=rc, tick=15).fire


def test_empty_corpus_is_max_novelty(rng):
    d = delta_gate(rng.randn(32), [], novelty_min=0.15)
    assert d.fire and d.novelty == 1.0


def test_numeric_only_decision():
    assert delta_gate(None, numeric_revision=0.3, numeric_revision_min=0.05).fire
    assert not delta_gate(None, numeric_revision=0.0).fire


def test_cosine_novelty_zero_vector():
    assert cosine_novelty([0.0, 0.0, 0.0], [[1.0, 0.0, 0.0]]) == 0.0
