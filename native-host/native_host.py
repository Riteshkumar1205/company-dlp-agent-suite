"""
Native messaging host. Reads length-prefixed JSON messages from stdin, forwards to local agent.
Build to exe with PyInstaller and register host manifest for Chrome/Firefox.
"""

import sys, struct, json, requests, logging, os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("native_host")
AGENT_LOCAL_ENDPOINT = os.environ.get("AGENT_LOCAL_ENDPOINT", "http://127.0.0.1:7010/native/events")

def read_message():
    raw_len = sys.stdin.buffer.read(4)
    if not raw_len:
        return None
    msg_len = struct.unpack('<I', raw_len)[0]
    data = sys.stdin.buffer.read(msg_len).decode('utf-8')
    return json.loads(data)

def send_response(obj):
    data = json.dumps(obj).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('<I', len(data)))
    sys.stdout.buffer.write(data)
    sys.stdout.flush()

def forward(payload):
    try:
        resp = requests.post(AGENT_LOCAL_ENDPOINT, json=payload, timeout=2)
        resp.raise_for_status()
        return True
    except Exception:
        logger.exception("forward failed")
        return False

def main():
    while True:
        msg = read_message()
        if msg is None:
            break
        logger.info("native received: %s", msg)
        ok = forward({"event_type":"browser_upload_attempt", "payload": msg})
        send_response({"status": "ok" if ok else "failed"})

if __name__ == '__main__':
    main()
