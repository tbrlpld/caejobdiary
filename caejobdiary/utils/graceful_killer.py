import logging
import signal


class GracefulKiller():
    """
    Informant about reception of termination signals
    """

    kill_now = False

    def __init__(self, name):
        self.logger = logging.getLogger(__name__).getChild(name)
        # print(__name__)
        self.logger.debug("Creating kill signal listeners.")
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        signal.signal(signal.SIGINT, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.logger.info("Received termination signal.")
        self.kill_now = True
