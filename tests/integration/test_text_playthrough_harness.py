import os

import pytest

from textPlaythrough import (
    BOOT_TIMEOUT_ENV_VAR,
    DEFAULT_BOOT_TIMEOUT,
    TextPlaythrough,
    resolveBootTimeout,
)

# Unlike test_text_playthrough.py these never launch the game, so they run
# everywhere except where noted — the harness's own logic is worth guarding on
# a Windows dev machine too.


class FakeProcess:
    """Stands in for the Popen the harness owns. `stderr` is None here; the
    real stream is exercised by the pipe-backed test below."""

    def __init__(self, returnCode):
        self._returnCode = returnCode
        self.stderr = None

    def poll(self):
        return self._returnCode


def test_boot_timeout_defaults_when_nothing_overrides_it(monkeypatch):
    monkeypatch.delenv(BOOT_TIMEOUT_ENV_VAR, raising=False)
    assert resolveBootTimeout() == DEFAULT_BOOT_TIMEOUT


def test_boot_timeout_reads_the_environment_variable(monkeypatch):
    monkeypatch.setenv(BOOT_TIMEOUT_ENV_VAR, "45")
    assert resolveBootTimeout() == 45.0


def test_an_explicit_boot_timeout_beats_the_environment_variable(monkeypatch):
    # runScript's kwarg and roamScript.py's --boot-timeout are per-run
    # decisions; a machine-wide export must not silently override them.
    monkeypatch.setenv(BOOT_TIMEOUT_ENV_VAR, "45")
    assert resolveBootTimeout(3) == 3.0


@pytest.mark.parametrize("value", ["", "soon", "0", "-5"])
def test_an_unusable_environment_value_falls_back_to_the_default(monkeypatch, value):
    # A typo in a shell export should not make every playthrough fail in a way
    # that reads like a game bug.
    monkeypatch.setenv(BOOT_TIMEOUT_ENV_VAR, value)
    assert resolveBootTimeout() == DEFAULT_BOOT_TIMEOUT


def test_the_harness_picks_up_the_environment_variable(monkeypatch):
    # The payoff: both integration modules construct the harness bare, so this
    # is the only lever that reaches a whole pytest run.
    monkeypatch.setenv(BOOT_TIMEOUT_ENV_VAR, "30")
    assert TextPlaythrough()._bootTimeout == 30.0


def test_describe_child_reports_a_process_that_never_started():
    assert TextPlaythrough().describeChild() == "child: not started"


def test_describe_child_reports_a_running_process():
    game = TextPlaythrough()
    game._proc = FakeProcess(None)
    assert game.describeChild() == "child: still running, no stderr"


def test_describe_child_reports_an_exit_code():
    game = TextPlaythrough()
    game._proc = FakeProcess(1)
    assert game.describeChild() == "child: exited with code 1, no stderr"


@pytest.mark.skipif(os.name != "posix", reason="select() on a pipe is POSIX-only")
def test_describe_child_quotes_stderr_written_before_the_failure():
    # The case that motivated this: the child is alive but has already printed
    # a traceback, and nothing was ever painted to the pty.
    readFd, writeFd = os.pipe()
    game = TextPlaythrough()
    game._proc = FakeProcess(None)
    game._proc.stderr = os.fdopen(readFd, "rb")
    try:
        os.write(writeFd, b"Traceback (most recent call last):\n")
        described = game.describeChild()
    finally:
        os.close(writeFd)
        game._proc.stderr.close()
    assert described.startswith("child: still running, stderr:")
    assert "Traceback (most recent call last):" in described


@pytest.mark.skipif(os.name != "posix", reason="select() on a pipe is POSIX-only")
def test_expect_timeout_message_names_the_child_state():
    # Without this the message is just "timed out ... last output:" followed by
    # nothing, which is indistinguishable from a rendering bug.
    readFd, writeFd = os.pipe()
    game = TextPlaythrough()
    game._master = readFd
    game._proc = FakeProcess(3)
    try:
        with pytest.raises(AssertionError) as failure:
            game.expect("Roam", timeout=0.3)
    finally:
        os.close(readFd)
        os.close(writeFd)
    assert "child: exited with code 3" in str(failure.value)
