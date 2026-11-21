"""The composition root wires the production adapters by default and lets a
caller override either one."""

import json

from agenticFakes import FakeLanguageModel, InlineRunner
from npc.agentic import service
from npc.agentic.adapters.anthropicLanguageModel import AnthropicLanguageModel
from npc.agentic.adapters.daemonThreadRunner import DaemonThreadRunner
from npc.agentic.adapters.openAiCompatibleLanguageModel import (
    OpenAiCompatibleLanguageModel,
)
from npc.agentic.core import _SYSTEM_PROMPT, AgenticBehavior
from npc.agentic.model import Completion


def test_defaults_to_the_environment_model_and_a_daemon_runner(monkeypatch):
    monkeypatch.delenv("ROAM_NPC_MODEL_URL", raising=False)
    sentinel = object()
    monkeypatch.setattr(
        AnthropicLanguageModel, "fromEnvironment", staticmethod(lambda: sentinel)
    )

    behavior = service.createAgenticBehavior()

    assert isinstance(behavior, AgenticBehavior)
    assert behavior._model is sentinel
    assert isinstance(behavior._runner, DaemonThreadRunner)


def test_no_key_means_no_model(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ROAM_NPC_MODEL_URL", raising=False)
    assert service.createAgenticBehavior()._model is None


def test_an_openai_compatible_url_wins_over_the_anthropic_key(monkeypatch):
    monkeypatch.setenv("ROAM_NPC_MODEL_URL", "http://127.0.0.1:9/v1")
    monkeypatch.setattr(
        AnthropicLanguageModel, "fromEnvironment", staticmethod(lambda: object())
    )

    model = service.createAgenticBehavior()._model

    assert isinstance(model, OpenAiCompatibleLanguageModel)
    assert model.getEndpoint() == "http://127.0.0.1:9/v1/chat/completions"


def test_without_a_url_the_anthropic_model_is_used(monkeypatch):
    sentinel = object()
    monkeypatch.delenv("ROAM_NPC_MODEL_URL", raising=False)
    monkeypatch.setattr(
        AnthropicLanguageModel, "fromEnvironment", staticmethod(lambda: sentinel)
    )
    assert service.createAgenticBehavior()._model is sentinel


def test_overrides_are_used_as_given():
    model = FakeLanguageModel(Completion.ok("{}"))
    runner = InlineRunner()

    behavior = service.createAgenticBehavior(model=model, runner=runner)

    assert behavior._model is model
    assert behavior._runner is runner


def test_core_runs_a_call_through_the_ports():
    reply = json.dumps({"goal": "explore", "actions": [{"type": "idle"}]})
    model = FakeLanguageModel(Completion.ok(reply))
    behavior = service.createAgenticBehavior(model=model, runner=InlineRunner())

    behavior._callAI("state")

    assert model.requests == [(_SYSTEM_PROMPT, "state")]
    assert behavior.getGoalDescription() == "explore"
    assert behavior._actionQueue.get_nowait() == {"type": "idle"}


def test_core_drops_a_failed_completion_and_clears_the_pending_flag():
    model = FakeLanguageModel(Completion.failed("offline"))
    behavior = service.createAgenticBehavior(model=model, runner=InlineRunner())
    behavior._pendingCall = True

    behavior._callAI("state")

    assert behavior._actionQueue.empty()
    assert behavior._pendingCall is False
