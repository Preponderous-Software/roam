import os

try:
    import anthropic as _anthropic_module

    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False

from npc.agentic.model import Completion
from npc.agentic.ports.languageModel import LanguageModel

_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 512


class AnthropicLanguageModel(LanguageModel):
    """`LanguageModel` backed by the Anthropic Messages API."""

    def __init__(self, client):
        self._client = client

    @staticmethod
    def fromEnvironment():
        """Build from ANTHROPIC_API_KEY, or return None when the `anthropic`
        package is missing, the key is unset, or the client can't be built."""
        client = AnthropicLanguageModel._buildClient()
        if client is None:
            return None
        return AnthropicLanguageModel(client)

    @staticmethod
    def _buildClient():
        if not _ANTHROPIC_AVAILABLE:
            return None
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            return None
        try:
            return _anthropic_module.Anthropic(api_key=key)
        except Exception:
            return None

    def complete(self, systemPrompt, userMessage):
        try:
            response = self._client.messages.create(
                model=_MODEL,
                max_tokens=_MAX_TOKENS,
                system=systemPrompt,
                messages=[{"role": "user", "content": userMessage}],
            )
            text = next((b.text for b in response.content if b.type == "text"), "{}")
        except Exception as exc:
            return Completion.failed(str(exc))
        return Completion.ok(text)
