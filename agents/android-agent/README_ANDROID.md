Android Agent (skeleton)

- Open `agents/android-agent/skeleton` in Android Studio.
- Implement Device Owner provisioning (EMM or `adb dpm set-device-owner` for lab).
- Implement DevicePolicyManager calls for:
  - disabling OTG
  - restricting clipboard interactions between work & personal profiles
  - per-app VPN for managed apps
- Use managed Google Play to distribute the app for enterprise.
