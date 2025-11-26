#!/usr/bin/env python3
"""
Onboarding wizard (cross-platform tkinter)
- Registers device with backend
- Requests OTP and verifies
- Collects admin emails
- Saves encrypted config via shared.utils.crypto
"""

import tkinter as tk
from tkinter import messagebox
import hashlib
import json
import uuid
import requests
import platform
import time
from pathlib import Path

# repo root path insert if running from repo
ROOT = Path(__file__).resolve().parents[2]
import os, sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.utils.crypto import encrypt_json, ensure_key

# default server (change to your production URL)
SERVER = "http://127.0.0.1:8443"

# config paths
WIN_CFG_DIR = Path("C:/ProgramData/CompanyAgent/config")
WIN_CFG_FILE = WIN_CFG_DIR / "agent_config.enc"
LIN_CFG_DIR = Path("/opt/company-agent/config")
LIN_CFG_FILE = LIN_CFG_DIR / "agent_config.enc"

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def get_paths():
    if platform.system().lower().startswith("windows"):
        return WIN_CFG_DIR, WIN_CFG_FILE
    else:
        return LIN_CFG_DIR, LIN_CFG_FILE

def save_encrypted_config(cfg: dict):
    cfg_dir, cfg_file = get_paths()
    cfg_dir.mkdir(parents=True, exist_ok=True)
    enc = encrypt_json(cfg)
    cfg_file.write_bytes(enc)
    try:
        if not platform.system().lower().startswith("windows"):
            os.chmod(str(cfg_file), 0o600)
    except Exception:
        pass

class OnboardingWizard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Company DLP - Activation Required")
        self.root.geometry("480x400")

        tk.Label(self.root, text="Employee Email").pack(pady=4)
        self.email = tk.Entry(self.root, width=60); self.email.pack()
        tk.Label(self.root, text="Password").pack(pady=4)
        self.pw = tk.Entry(self.root, show="*", width=60); self.pw.pack()
        tk.Label(self.root, text="Confirm Password").pack(pady=4)
        self.pw2 = tk.Entry(self.root, show="*", width=60); self.pw2.pack()
        tk.Label(self.root, text="Admin Emails (comma separated)").pack(pady=4)
        self.admins = tk.Entry(self.root, width=60); self.admins.pack()
        tk.Label(self.root, text="OTP (enter after Request OTP)").pack(pady=4)
        self.otp = tk.Entry(self.root, width=30); self.otp.pack()

        tk.Button(self.root, text="Request OTP", command=self.request_otp).pack(pady=6)
        tk.Button(self.root, text="Activate", command=self.activate).pack(pady=6)

        self.temp_device_id = None

    def request_otp(self):
        email = self.email.get().strip()
        if not email:
            messagebox.showerror("Error", "Enter email")
            return
        # register device on backend
        device_id = str(uuid.uuid4())
        try:
            r = requests.post(f"{SERVER}/api/v1/register_device", json={"employee_email": email, "device_id": device_id}, timeout=5)
            r.raise_for_status()
        except Exception as e:
            messagebox.showerror("Register failed", str(e))
            return
        # request OTP
        try:
            r = requests.post(f"{SERVER}/api/v1/request_otp", json={"email": email, "device_id": device_id}, timeout=5)
            if r.status_code == 200 and r.json().get("sent"):
                messagebox.showinfo("OTP", "OTP requested; check email")
                self.temp_device_id = device_id
            else:
                messagebox.showerror("OTP", "OTP request failed")
        except Exception as e:
            messagebox.showerror("OTP error", str(e))

    def activate(self):
        email = self.email.get().strip()
        pw1 = self.pw.get().strip()
        pw2 = self.pw2.get().strip()
        admins = [x.strip() for x in self.admins.get().split(",") if x.strip()]
        otp = self.otp.get().strip()

        if not email or not pw1 or pw1 != pw2:
            messagebox.showerror("Error", "Invalid email or passwords mismatch")
            return
        if not self.temp_device_id:
            messagebox.showerror("Error", "Request OTP first")
            return
        # verify otp
        try:
            r = requests.post(f"{SERVER}/api/v1/verify_otp", json={"device_id": self.temp_device_id, "code": otp}, timeout=5)
            r.raise_for_status()
            ok = r.json().get("ok")
            if not ok:
                messagebox.showerror("OTP", "Invalid OTP")
                return
        except Exception as e:
            messagebox.showerror("OTP verify failed", str(e))
            return

        # get binding info (mac/serial) best-effort
        mac = None; serial = None
        try:
            if platform.system().lower().startswith("linux"):
                try:
                    serial = Path("/sys/class/dmi/id/product_serial").read_text().strip()
                except Exception:
                    serial = None
                # mac pick from interfaces
                try:
                    import netifaces
                    for iface in netifaces.interfaces():
                        addrs = netifaces.ifaddresses(iface).get(netifaces.AF_LINK)
                        if addrs:
                            mac = addrs[0].get('addr')
                            if mac:
                                break
                except Exception:
                    mac = None
            else:
                try:
                    import wmi
                    c = wmi.WMI()
                    for bios in c.Win32_BIOS():
                        serial = bios.SerialNumber
                    for nic in c.Win32_NetworkAdapterConfiguration(IPEnabled=True):
                        if nic.MACAddress:
                            mac = nic.MACAddress
                            break
                except Exception:
                    pass
        except Exception:
            pass

        cfg = {
            "activated": True,
            "employee_email": email,
            "employee_password_hash": hash_password(pw1),
            "admin_emails": admins,
            "device_id": self.temp_device_id,
            "server_url": SERVER,
            "lockdown_enabled": False,
            "bound": True if mac or serial else False,
            "bound_info": {"mac": mac, "serial": serial},
            "last_login": int(time.time()),
            "force_login_interval_seconds": 24*3600,
            "agent_version": "1.0.0"
        }

        # send binding info, best-effort, to admin endpoints
        try:
            requests.post(f"{SERVER}/admin/devices/{self.temp_device_id}/bind", json={"mac": mac, "serial": serial}, timeout=3)
        except Exception:
            pass

        save_encrypted_config(cfg)
        messagebox.showinfo("Activated", "Device activated. DLP agent will start.")
        self.root.destroy()

def hash_password(pw: str):
    import hashlib
    return hashlib.sha256(pw.encode()).hexdigest()

if __name__ == "__main__":
    OnboardingWizard().root.mainloop()
