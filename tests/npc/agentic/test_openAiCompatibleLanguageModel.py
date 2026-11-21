"""OpenAiCompatibleLanguageModel against a real HTTP server on 127.0.0.1."""

import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from npc.agentic.adapters.openAiCompatibleLanguageModel import (
    KEY_VARIABLE,
    NAME_VARIABLE,
    TIMEOUT_VARIABLE,
    URL_VARIABLE,
    OpenAiCompatibleLanguageModel,
)


class _Server:
    """A one-route chat-completions stand-in that records each request."""

    def __init__(self):
        self.status = 200
        self.body = b"{}"
        self.requests = []
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                server.requests.append(
                    {
                        "path": self.path,
                        "headers": dict(self.headers),
                        "json": json.loads(self.rfile.read(length)),
                    }
                )
                self.send_response(server.status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(server.body)

            def log_message(self, *args):
                pass

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.baseUrl = "http://127.0.0.1:%d/v1" % self._httpd.server_address[1]
        threading.Thread(
            target=self._httpd.serve_forever, args=(0.01,), daemon=True
        ).start()

    def reply(self, content, status=200):
        self.status = status
        self.body = json.dumps(
            {"choices": [{"message": {"role": "assistant", "content": content}}]}
        ).encode()

    def close(self):
        self._httpd.shutdown()
        self._httpd.server_close()


@pytest.fixture
def server():
    s = _Server()
    yield s
    s.close()


def test_returns_the_first_choice_text(server):
    server.reply('{"goal": "g", "actions": []}')
    completion = OpenAiCompatibleLanguageModel(server.baseUrl).complete("sys", "u")
    assert completion.isOk()
    assert completion.getText() == '{"goal": "g", "actions": []}'


def test_sends_a_chat_completions_request(server):
    server.reply("{}")
    model = OpenAiCompatibleLanguageModel(
        server.baseUrl + "/", apiKey="k-123", modelName="qwen-small"
    )

    model.complete("the system prompt", "the world state")

    (request,) = server.requests
    assert request["path"] == "/v1/chat/completions"
    assert request["headers"]["Authorization"] == "Bearer k-123"
    assert request["headers"]["Content-Type"] == "application/json"
    assert request["json"] == {
        "model": "qwen-small",
        "max_tokens": 512,
        "messages": [
            {"role": "system", "content": "the system prompt"},
            {"role": "user", "content": "the world state"},
        ],
    }


def test_sends_no_authorization_header_without_a_key(server):
    server.reply("{}")
    OpenAiCompatibleLanguageModel(server.baseUrl).complete("s", "u")
    (request,) = server.requests
    assert "Authorization" not in request["headers"]
    assert request["json"]["model"] == "default"


@pytest.mark.parametrize("content", [None, ""])
def test_a_reply_without_text_is_an_empty_object(server, content):
    server.reply(content)
    completion = OpenAiCompatibleLanguageModel(server.baseUrl).complete("s", "u")
    assert completion.isOk()
    assert completion.getText() == "{}"


def test_an_http_error_is_a_failed_completion(server):
    server.reply("ignored", status=503)
    completion = OpenAiCompatibleLanguageModel(server.baseUrl).complete("s", "u")
    assert not completion.isOk()
    assert "503" in completion.getReason()


@pytest.mark.parametrize("body", [b"not json", b'{"choices": []}', b"{}"])
def test_a_malformed_reply_is_a_failed_completion(server, body):
    server.body = body
    completion = OpenAiCompatibleLanguageModel(server.baseUrl).complete("s", "u")
    assert not completion.isOk()


def test_an_unreachable_server_is_a_failed_completion(server):
    url = server.baseUrl
    server.close()
    completion = OpenAiCompatibleLanguageModel(url).complete("s", "u")
    assert not completion.isOk()
    assert completion.getReason()


# ------------------------------------------------------------------ #
# fromEnvironment                                                      #
# ------------------------------------------------------------------ #


@pytest.fixture
def cleanEnvironment(monkeypatch):
    for name in (URL_VARIABLE, KEY_VARIABLE, NAME_VARIABLE, TIMEOUT_VARIABLE):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


@pytest.mark.parametrize("value", [None, "", "   "])
def test_from_environment_is_none_without_a_url(cleanEnvironment, value):
    if value is not None:
        cleanEnvironment.setenv(URL_VARIABLE, value)
    assert OpenAiCompatibleLanguageModel.fromEnvironment() is None


def test_from_environment_reads_url_key_and_name(cleanEnvironment, server):
    server.reply("{}")
    cleanEnvironment.setenv(URL_VARIABLE, server.baseUrl)
    cleanEnvironment.setenv(KEY_VARIABLE, "secret")
    cleanEnvironment.setenv(NAME_VARIABLE, "local-model")

    model = OpenAiCompatibleLanguageModel.fromEnvironment()
    model.complete("s", "u")

    assert model.getEndpoint() == server.baseUrl + "/chat/completions"
    (request,) = server.requests
    assert request["headers"]["Authorization"] == "Bearer secret"
    assert request["json"]["model"] == "local-model"


@pytest.mark.parametrize(
    "value, expected",
    [(None, 60), ("", 60), ("abc", 60), ("0", 60), ("-5", 60), ("180", 180.0)],
)
def test_from_environment_timeout(cleanEnvironment, value, expected):
    cleanEnvironment.setenv(URL_VARIABLE, "http://127.0.0.1:9/v1")
    if value is not None:
        cleanEnvironment.setenv(TIMEOUT_VARIABLE, value)
    model = OpenAiCompatibleLanguageModel.fromEnvironment()
    assert model.getTimeoutSeconds() == expected


def test_a_server_that_never_answers_times_out_as_a_failed_completion():
    # A listening socket that accepts the connection but never replies.
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    try:
        url = "http://127.0.0.1:%d/v1" % listener.getsockname()[1]
        model = OpenAiCompatibleLanguageModel(url, timeoutSeconds=0.2)
        start = time.monotonic()
        completion = model.complete("s", "u")
        elapsed = time.monotonic() - start
    finally:
        listener.close()
    assert elapsed < 5
    assert not completion.isOk()
    assert "timed out" in completion.getReason()
