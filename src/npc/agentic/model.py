"""Plain values exchanged between the agentic core and its ports. No I/O."""


class Completion:
    """What a `LanguageModel` returned for one request.

    A failed call is an expected outcome, so it is a value here, not an
    exception: `isOk()` is False and `getReason()` says why.
    """

    def __init__(self, text, reason):
        self._text = text
        self._reason = reason

    @staticmethod
    def ok(text):
        return Completion(text, None)

    @staticmethod
    def failed(reason):
        return Completion(None, reason)

    def isOk(self):
        return self._reason is None

    def getText(self):
        return self._text

    def getReason(self):
        return self._reason
