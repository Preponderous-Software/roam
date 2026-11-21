"""Contract tests: every LanguageModel / BackgroundRunner implementation,
fake or production, must pass the same checks."""

import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agenticFakes import FakeLanguageModel, InlineRunner
from npc.agentic.adapters.anthropicLanguageModel import AnthropicLanguageModel
from npc.agentic.adapters.daemonThreadRunner import DaemonThreadRunner
from npc.agentic.model import Completion


def _sdkStub(content=None, error=None):
    create = MagicMock(
        side_effect=error,
        return_value=SimpleNamespace(content=content or []),
    )
    return SimpleNamespace(messages=SimpleNamespace(create=create))


def _textBlock(text):
    return SimpleNamespace(type="text", text=text)


# ------------------------------------------------------------------ #
# LanguageModel                                                        #
# ------------------------------------------------------------------ #


def _answering(kind, text):
    if kind == "fake":
        return FakeLanguageModel(Completion.ok(text))
    return AnthropicLanguageModel(_sdkStub(content=[_textBlock(text)]))


def _failing(kind, reason):
    if kind == "fake":
        return FakeLanguageModel(Completion.failed(reason))
    return AnthropicLanguageModel(_sdkStub(error=RuntimeError(reason)))


@pytest.mark.parametrize("kind", ["fake", "anthropic"])
def test_language_model_returns_the_reply_text(kind):
    completion = _answering(kind, '{"goal": "g"}').complete("sys", "user")
    assert completion.isOk()
    assert completion.getText() == '{"goal": "g"}'
    assert completion.getReason() is None


@pytest.mark.parametrize("kind", ["fake", "anthropic"])
def test_language_model_reports_failure_as_a_value(kind):
    completion = _failing(kind, "rate limited").complete("sys", "user")
    assert not completion.isOk()
    assert completion.getReason() == "rate limited"
    assert completion.getText() is None


def test_anthropic_reply_without_a_text_block_is_an_empty_object():
    model = AnthropicLanguageModel(
        _sdkStub(content=[SimpleNamespace(type="thinking", text="x")])
    )
    assert model.complete("sys", "user").getText() == "{}"


def test_anthropic_uses_the_first_text_block():
    model = AnthropicLanguageModel(
        _sdkStub(content=[_textBlock("first"), _textBlock("second")])
    )
    assert model.complete("sys", "user").getText() == "first"


def test_anthropic_from_environment_is_none_without_a_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert AnthropicLanguageModel.fromEnvironment() is None


# ------------------------------------------------------------------ #
# BackgroundRunner                                                     #
# ------------------------------------------------------------------ #


@pytest.mark.parametrize("runner", [InlineRunner(), DaemonThreadRunner()])
def test_runner_runs_the_target_with_its_args(runner):
    done = threading.Event()
    received = []

    def target(a, b):
        received.append((a, b))
        done.set()

    runner.start(target, (1, "two"))

    assert done.wait(timeout=5)
    assert received == [(1, "two")]


def test_daemon_runner_does_not_keep_the_process_alive():
    seen = []
    done = threading.Event()

    def target():
        seen.append(threading.current_thread().daemon)
        done.set()

    DaemonThreadRunner().start(target, ())

    assert done.wait(timeout=5)
    assert seen == [True]
