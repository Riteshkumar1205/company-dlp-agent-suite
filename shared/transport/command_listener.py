import threading, time, logging

logger = logging.getLogger("transport.command_listener")
ALLOWED_COMMANDS = {"WARN_USER", "QUARANTINE_FILE", "DISABLE_USB", "DISABLE_UPLOAD", "BLOCK_TRANSFER"}

class CommandListener:
    def __init__(self, sender, device_id: str, poll_interval=10):
        self.sender = sender
        self.device_id = device_id
        self.poll_interval = poll_interval
        self.running = False
        self.thread = None

    def poll_once(self):
        url = f"{self.sender.base_url}/api/v1/agents/{self.device_id}/commands"
        resp = self.sender.session.get(url, headers=self.sender._headers(), cert=self.sender.client_cert, verify=self.sender.ca_bundle or True, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def handle_command(self, cmd: dict):
        typ = cmd.get("type")
        if typ not in ALLOWED_COMMANDS:
            logger.warning("Forbidden command: %s", typ)
            return
        logger.info("Handling command: %s", typ)

    def _loop(self):
        while self.running:
            try:
                cmds = self.poll_once()
                for c in cmds:
                    try:
                        self.handle_command(c)
                    except Exception:
                        logger.exception("command handling failed")
            except Exception:
                logger.exception("command poll error")
            time.sleep(self.poll_interval)

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
