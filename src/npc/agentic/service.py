"""Composition root for the agentic NPC: wires the production adapters."""

from npc.agentic.adapters.anthropicLanguageModel import AnthropicLanguageModel
from npc.agentic.adapters.daemonThreadRunner import DaemonThreadRunner
from npc.agentic.core import AgenticBehavior

_FROM_ENVIRONMENT = object()


def createAgenticBehavior(model=_FROM_ENVIRONMENT, runner=None):
    """Build an AgenticBehavior.

    `model` defaults to the Anthropic API when ANTHROPIC_API_KEY is set (and
    to None, the ProgrammaticBehavior fallback, otherwise). `runner` defaults
    to a daemon thread per call. Pass either to override it.
    """
    if model is _FROM_ENVIRONMENT:
        model = AnthropicLanguageModel.fromEnvironment()
    if runner is None:
        runner = DaemonThreadRunner()
    return AgenticBehavior(model, runner)
