"""web/serve.py routes: the index aliases answer GET and HEAD alike."""

import threading
import urllib.error
import urllib.request

import pytest

import serve


@pytest.fixture(scope="module")
def base_url():
    server = serve._Server(("127.0.0.1", 0), serve._Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def _request(url, method):
    return urllib.request.urlopen(urllib.request.Request(url, method=method))


@pytest.mark.parametrize("path", ["/", "/play", "/play/", "/index.html"])
def test_index_aliases_answer_get_and_head(base_url, path):
    with _request(base_url + path, "GET") as get:
        body = get.read()
        assert get.status == 200
    with _request(base_url + path, "HEAD") as head:
        assert head.status == 200
        assert head.read() == b""
        assert head.headers["Content-Length"] == str(len(body))
        assert head.headers["Cross-Origin-Embedder-Policy"] == "require-corp"


def test_unknown_path_is_404_for_head_too(base_url):
    with pytest.raises(urllib.error.HTTPError) as error:
        _request(base_url + "/no-such-page", "HEAD")
    assert error.value.code == 404


def test_a_tap_sends_mouse_up_with_coordinates_captured_before_reset():
    # The touchend handler clears _tapStart right after scheduling the
    # delayed mouse_up; the callback must not read _tapStart (it is null by
    # then, which threw and dropped every tap's mouse_up).
    import os
    import re

    page = open(
        os.path.join(os.path.dirname(__file__), "..", "..", "web", "index.html")
    ).read()
    delayed = re.findall(
        r"setTimeout\(\(\) => sendMouseEvent\(\"mouse_up\", ([^)]*)\)", page
    )
    assert delayed, "no delayed mouse_up found"
    for args in delayed:
        assert "_tapStart" not in args, args
