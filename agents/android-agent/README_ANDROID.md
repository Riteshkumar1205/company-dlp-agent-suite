Android Agent skeleton (Device Owner)
- Open skeleton/ in Android Studio
- Implement Device Owner provisioning (EMM or adb dpm)
- Use DevicePolicyManager APIs to restrict OTG, clipboard flows, and configure a per-app VPN for managed apps
- Use Work Profile for BYOD or Device Owner for corp-owned devices
- Integrate with backend via HTTPS + certificate authentication (mTLS recommended)
