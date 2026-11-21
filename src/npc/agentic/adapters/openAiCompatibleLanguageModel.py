import json
import os
import urllib.request

from npc.agentic.model import Completion
from npc.agentic.ports.languageModel import LanguageModel

URL_VARIABLE = "ROAM_NPC_MODEL_URL"
KEY_VARIABLE = "ROAM_NPC_MODEL_KEY"
NAME_VARIABLE = "ROAM_NPC_MODEL_NAME"
TIMEOUT_VARIABLE = "ROAM_NPC_MODEL_TIMEOUT"

_DEFAULT_NAME = "default"
_MAX_TOKENS = 512
_TIMEOUT_SECONDS = 60


class OpenAiCompatibleLanguageModel(LanguageModel):
    """`LanguageModel` backed by any server that speaks the OpenAI chat
    completions API (`POST <baseUrl>/chat/completions`), such as a self-hosted
    llama.cpp `llama-server`, Ollama, vLLM or LM Studio.

    Uses only the standard library. `baseUrl` is the API root, normally ending
    in `/v1` (e.g. `http://localhost:8080/v1`). `apiKey`, when given, is sent
    as a bearer token. `modelName` is sent as `model`; servers that host a
    single model usually ignore it. `timeoutSeconds` bounds each request; the
    call runs off the game thread, so a slow server delays the next plan but
    never stalls the game.
    """

    def __init__(self, baseUrl, apiKey=None, modelName=None, timeoutSeconds=None):
        self._endpoint = baseUrl.rstrip("/") + "/chat/completions"
        self._apiKey = apiKey
        self._modelName = modelName or _DEFAULT_NAME
        self._timeoutSeconds = timeoutSeconds or _TIMEOUT_SECONDS

    @staticmethod
    def fromEnvironment():
        """Build from ROAM_NPC_MODEL_URL (plus the optional ROAM_NPC_MODEL_KEY,
        ROAM_NPC_MODEL_NAME and ROAM_NPC_MODEL_TIMEOUT in seconds), or return
        None when the URL is unset. A timeout that is not a positive number
        falls back to the default."""
        baseUrl = os.environ.get(URL_VARIABLE, "").strip()
        if not baseUrl:
            return None
        return OpenAiCompatibleLanguageModel(
            baseUrl,
            apiKey=os.environ.get(KEY_VARIABLE, "").strip() or None,
            modelName=os.environ.get(NAME_VARIABLE, "").strip() or None,
            timeoutSeconds=_positiveNumber(os.environ.get(TIMEOUT_VARIABLE)),
        )

    def getEndpoint(self):
        return self._endpoint

    def getTimeoutSeconds(self):
        return self._timeoutSeconds

    def complete(self, systemPrompt, userMessage):
        body = json.dumps(
            {
                "model": self._modelName,
                "max_tokens": _MAX_TOKENS,
                "messages": [
                    {"role": "system", "content": systemPrompt},
                    {"role": "user", "content": userMessage},
                ],
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self._apiKey:
            headers["Authorization"] = "Bearer " + self._apiKey
        request = urllib.request.Request(
            self._endpoint, data=body, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeoutSeconds) as reply:
                data = json.loads(reply.read().decode("utf-8"))
            text = data["choices"][0]["message"].get("content")
        except Exception as exc:
            return Completion.failed(str(exc))
        return Completion.ok(text or "{}")


def _positiveNumber(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None
