#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows Agent (updated)
- Encrypted config at C:\ProgramData\CompanyAgent\config\agent_config.enc
- Onboarding wizard invoked when not activated
- Force-login (re-onsboard after interval)
- Policy sync, update poller, OTP binding support
- Uses shared utils and shared.transport sender/command_listener
"""

import argparse
import json
import logging
import os
import platform
import threading
import time
from pathlib import Path

# Prep repo root for imports (when running from repo)
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(ROOT))

# Shared modules
from shared.utils.crypto import decrypt_bytes, encrypt_json, ensure_key
from shared.transport.sender import SecureSender
from shared.transport.command_listener import CommandListener
from shared.processing.metadata import build_event_for_file, build_event_from_clipboard

# Core watchers (these modules were provided previously; keep under core/)
from core.event_watcher import start_filesystem_watcher
from core.screenshot_detector import start_screenshot_monitor
from core.clipboard_monitor import start_clipboard_monitor
from core.usb_monitor import start_usb_monitor
from core.foreground import get_foreground_process_info

# Onboarding wizard
from onboarding.onboarding_wizard import OnboardingWizard, get_mac_and_serial

LOG_DIR = Path("C:/ProgramData/CompanyAgent/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename=str(LOG_DIR / "agent.log"), level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("CompanyAgent")

CONFIG_DIR = Path("C:/ProgramData/CompanyAgent/config")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
ENC_CONFIG_FILE = CONFIG_DIR / "agent_config.enc"

# Default fallback config (used for first-run inside repo)
LOCAL_PLAIN_CONFIG = Path(__file__).parent / "config" / "agent_config.json"

def load_encrypted_config():
    """Read and decrypt the config. Fallback to local plain json for dev."""
    if ENC_CONFIG_FILE.exists():
        try:
            b = ENC_CONFIG_FILE.read_bytes()
            return decrypt_bytes(b)
        except Exception:
            logger.exception("Failed to decrypt config")
            return {}
    if LOCAL_PLAIN_CONFIG.exists():
        try:
            return json.loads(LOCAL_PLAIN_CONFIG.read_text())
        except Exception:
            return {}
    return {}

def save_encrypted_config(cfg: dict):
    enc = encrypt_json(cfg)
    ENC_CONFIG_FILE.write_bytes(enc)
    try:
        os.chmod(str(ENC_CONFIG_FILE), 0o600)
    except Exception:
        pass

# sender and listener placeholders
sender = None
command_listener = None

# --- event handlers ---
def handle_file_event(ev):
    try:
        cfg = load_encrypted_config()
        p = Path(ev.get("file_path"))
        if not p.exists():
            return
        event = build_event_for_file(p, device_id=cfg.get("device_id"), user_email=cfg.get("employee_email"), app=ev.get("app","unknown"), destination=ev.get("destination"))
        event["foreground_process"] = get_foreground_process_info()
        logger.info("File event: %s", event["file_name"])
        sender.send_event(event)
    except Exception:
        logger.exception("handle_file_event failed")

def handle_clipboard_event(ev):
    try:
        cfg = load_encrypted_config()
        event = build_event_from_clipboard(ev, device_id=cfg.get("device_id"), user_email=cfg.get("employee_email"))
        logger.info("Clipboard event")
        sender.send_event(event)
    except Exception:
        logger.exception("handle_clipboard_event failed")

# --- onboarding & activation flow ---
def run_onboarding_if_needed():
    cfg = load_encrypted_config()
    if not cfg.get("activated", False):
        logger.info("Device not activated. Launching onboarding wizard.")
        wiz = OnboardingWizard()
        wiz.run()
        # after wizard the encrypted config file will be written
        cfg = load_encrypted_config()
    return cfg

# --- policy sync thread ---
def sync_policy_periodically(server_url, interval=3600):
    import requests
    from pathlib import Path
    while True:
        try:
            if not server_url:
                time.sleep(interval)
                continue
            resp = requests.get(f"{server_url}/api/v1/policy", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                p = CONFIG_DIR / "policy_cache.json"
                p.write_text(json.dumps(data, indent=2))
        except Exception:
            logger.exception("policy sync failed")
        time.sleep(interval)

# --- update poller thread ---
def update_poller_thread(device_id, server_url, poll_interval=3600):
    import requests
    while True:
        try:
            if not server_url or not device_id:
                time.sleep(poll_interval)
                continue
            resp = requests.get(f"{server_url}/update/manifest/{device_id}", timeout=10)
            if resp.status_code == 200:
                manifest = resp.json()
                latest = manifest.get("latest_version")
                url = manifest.get("channels", {}).get("stable", {}).get("url")
                cfg = load_encrypted_config()
                local_ver = cfg.get("agent_version", "0.0.0")
                if latest and url and latest != local_ver:
                    # download update artifact to updates dir
                    try:
                        r = requests.get(url, stream=True, timeout=30)
                        out_dir = CONFIG_DIR.parent / "updates"
                        out_dir.mkdir(parents=True, exist_ok=True)
                        out_file = out_dir / f"update_{latest}.bin"
                        with open(out_file, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        cfg["pending_update"] = {"version": latest, "path": str(out_file)}
                        save_encrypted_config(cfg)
                        logger.info("Downloaded update %s", latest)
                    except Exception:
                        logger.exception("download update failed")
        except Exception:
            logger.exception("update poller error")
        time.sleep(poll_interval)

# --- start/stop ---
def run_foreground():
    global sender, command_listener

    cfg = run_onboarding_if_needed()
    if not cfg:
        logger.error("Missing config after onboarding, aborting.")
        return

    server = cfg.get("server_url")
    sender = SecureSender(base_url=server, client_cert=(cfg.get("client_cert"), cfg.get("client_key")) if cfg.get("client_cert") else None, jwt_token=cfg.get("jwt_token"), ca_bundle=cfg.get("ca_bundle"))
    command_listener = CommandListener(sender, device_id=cfg.get("device_id"), poll_interval=cfg.get("poll_interval_seconds", 10))
    command_listener.start()

    # start policy sync
    t_policy = threading.Thread(target=sync_policy_periodically, args=(server, 3600), daemon=True)
    t_policy.start()
    # start update poller
    t_update = threading.Thread(target=update_poller_thread, args=(cfg.get("device_id"), server, 3600), daemon=True)
    t_update.start()

    # watch user folders
    home = Path.home()
    watch_paths = [home / "Downloads", home / "Desktop", home / "Documents"]
    for p in watch_paths:
        p.mkdir(parents=True, exist_ok=True)

    observer = start_filesystem_watcher(watch_paths, handle_file_event, {})
    ss_t = threading.Thread(target=start_screenshot_monitor, args=(handle_file_event,), daemon=True)
    ss_t.start()
    cb_t = threading.Thread(target=start_clipboard_monitor, args=(handle_clipboard_event,), daemon=True)
    cb_t.start()
    usb_t = threading.Thread(target=start_usb_monitor, args=(handle_file_event,), daemon=True)
    usb_t.start()

    logger.info("Agent running. Watching paths: %s", ", ".join(str(x) for x in watch_paths))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Agent stopping")
        observer.stop()
        observer.join()
        command_listener.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-foreground", action="store_true", help="Run agent in foreground")
    args = parser.parse_args()
    if args.run_foreground:
        run_foreground()
    else:
        print("Wrap with NSSM or PyInstaller in production. Use --run-foreground to run interactively.")
