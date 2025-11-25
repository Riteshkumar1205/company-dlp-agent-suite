"""
Top-level launcher for development. Detects OS and runs appropriate agent.
In production packages, install the appropriate agent for that platform instead.
"""
import platform
import sys
from pathlib import Path

def run_windows():
    try:
        import agents.windows_agent.agent_service as win_service
        win_service.run_foreground()
    except Exception as e:
        print("Windows agent error:", e)

def run_linux():
    try:
        import agents.linux_agent.agent_main as linux_main
        linux_main.run_agent()
    except Exception as e:
        print("Linux agent error:", e)

def main():
    os_name = platform.system().lower()
    print("Detected OS:", os_name)
    if os_name.startswith("windows"):
        run_windows()
    elif os_name.startswith("linux"):
        run_linux()
    else:
        print("Unsupported platform for this launcher. Use platform-specific packaging (Android: use Android Studio).")

if __name__ == "__main__":
    main()
