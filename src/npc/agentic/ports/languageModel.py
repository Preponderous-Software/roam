from abc import ABC, abstractmethod


class LanguageModel(ABC):
    """Answers one prompt with text.

    Contract:
    - `complete(systemPrompt, userMessage)` returns a `model.Completion`.
    - Any failure to get an answer (network, auth, rate limit, an SDK error) is
      returned as `Completion.failed(reason)`; it never raises for those.
    - A reply with no text content is `Completion.ok("{}")`.
    - It blocks until the answer arrives, so the core only calls it from a
      `BackgroundRunner` task, never on the game thread.
    - One instance may be called from one background task at a time.
    """

    @abstractmethod
    def complete(self, systemPrompt, userMessage):
        """Return a `Completion` for `userMessage` under `systemPrompt`."""
