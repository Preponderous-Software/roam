import threading

from npc.agentic.ports.backgroundRunner import BackgroundRunner


class DaemonThreadRunner(BackgroundRunner):
    """Runs each task on a new daemon thread."""

    def start(self, target, args):
        threading.Thread(
            target=target,
            args=args,
            daemon=True,
        ).start()
