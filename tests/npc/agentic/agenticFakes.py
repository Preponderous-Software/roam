"""Test doubles for the agentic NPC ports."""

from npc.agentic.model import Completion
from npc.agentic.ports.backgroundRunner import BackgroundRunner
from npc.agentic.ports.languageModel import LanguageModel


class FakeLanguageModel(LanguageModel):
    """Returns a canned Completion and records every request."""

    def __init__(self, completion):
        self._completion = completion
        self.requests = []

    def complete(self, systemPrompt, userMessage):
        self.requests.append((systemPrompt, userMessage))
        return self._completion


class InlineRunner(BackgroundRunner):
    """Runs each task immediately on the calling thread and records it."""

    def __init__(self):
        self.started = []

    def start(self, target, args):
        self.started.append((target, args))
        target(*args)
