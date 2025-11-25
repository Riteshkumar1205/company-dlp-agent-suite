# Deployment Guide (summary)

- Windows:
  - Build CompanyAgent.exe via PyInstaller.
  - Use NSSM or Windows Service wrapper to install service.
  - Sign binaries and MSI via WiX.

- Linux:
  - Place full agent under /opt/company-agent, install systemd unit.
  - Use Debian packages or configuration management (Ansible).

- Android:
  - Use EMM/Device Owner provisioning; open `agents/android-agent/skeleton` in Android Studio.

- Backend:
  - Deploy FastAPI container behind TLS-terminating proxy (NGINX).
  - Use PostgreSQL for production (set DATABASE_URL).
