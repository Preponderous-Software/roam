"""achievements.arcadeBridge: a no-op without a sink, at most once per session
with one, and never raises whatever the sink does."""

import pytest

from achievements import arcadeBridge


@pytest.fixture(autouse=True)
def _fresh_bridge():
    arcadeBridge.reset()
    yield
    arcadeBridge.reset()


def _recordingSink():
    sent = []
    arcadeBridge.install(sent.append)
    return sent


def test_without_a_sink_every_call_is_a_no_op():
    assert not arcadeBridge.isActive()
    arcadeBridge.unlock("hearth", "Hearth")
    arcadeBridge.submitScore("most-days", 3)
    # Installing a sink afterwards does not replay anything.
    sent = _recordingSink()
    assert sent == []


def test_an_unlock_is_reported_once_per_session():
    sent = _recordingSink()
    arcadeBridge.unlock("hearth", "Hearth")
    arcadeBridge.unlock("hearth", "Hearth")
    assert sent == [{"kind": "unlock", "achievement": "hearth", "title": "Hearth"}]


def test_an_unlock_without_a_title_omits_it():
    sent = _recordingSink()
    arcadeBridge.unlock("hearth")
    assert sent == [{"kind": "unlock", "achievement": "hearth"}]


def test_a_score_is_reported_only_when_it_beats_the_last_report():
    sent = _recordingSink()
    for value in (3, 3, 2, 5):
        arcadeBridge.submitScore("most-days", value)
    assert [m["value"] for m in sent] == [3, 5]
    assert all(
        m == {"kind": "score", "board": "most-days", "value": m["value"]} for m in sent
    )


def test_boards_are_tracked_separately():
    sent = _recordingSink()
    arcadeBridge.submitScore("most-days", 4)
    arcadeBridge.submitScore("most-rooms", 4)
    assert [m["board"] for m in sent] == ["most-days", "most-rooms"]


def test_non_numeric_and_non_positive_scores_are_dropped():
    sent = _recordingSink()
    arcadeBridge.submitScore("most-days", None)
    arcadeBridge.submitScore("most-days", "lots")
    arcadeBridge.submitScore("most-days", 0)
    assert sent == []


def test_a_failing_sink_never_raises_and_is_not_retried():
    calls = []

    def broken(message):
        calls.append(message)
        raise RuntimeError("the page is gone")

    arcadeBridge.install(broken)
    arcadeBridge.unlock("hearth", "Hearth")
    arcadeBridge.unlock("hearth", "Hearth")
    arcadeBridge.submitScore("most-days", 2)
    assert len(calls) == 2
