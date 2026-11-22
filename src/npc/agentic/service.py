"""Composition root for the agentic NPC: wires the production adapters."""

from npc.agentic.adapters.anthropicLanguageModel import AnthropicLanguageModel
from npc.agentic.adapters.daemonThreadRunner import DaemonThreadRunner
from npc.agentic.adapters.openAiCompatibleLanguageModel import (
    OpenAiCompatibleLanguageModel,
)
from npc.agentic.core import AgenticBehavior

_FROM_ENVIRONMENT = object()


def modelFromEnvironment():
    """Pick the LanguageModel the environment asks for.

    ROAM_NPC_MODEL_URL (an OpenAI-compatible server) wins when set, then
    ANTHROPIC_API_KEY (the Anthropic API). With neither, None: the
    ProgrammaticBehavior fallback.
    """
    model = OpenAiCompatibleLanguageModel.fromEnvironment()
    if model is None:
        model = AnthropicLanguageModel.fromEnvironment()
    return model


def createAgenticBehavior(model=_FROM_ENVIRONMENT, runner=None):
    """Build an AgenticBehavior.

    `model` defaults to `modelFromEnvironment()`. `runner` defaults to a daemon
    thread per call. Pass either to override it.
    """
    if model is _FROM_ENVIRONMENT:
        model = modelFromEnvironment()
    if runner is None:
        runner = DaemonThreadRunner()
    return AgenticBehavior(model, runner)
