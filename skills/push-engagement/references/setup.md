# Push Setup and Credentials

Verified August 2026 against Expo SDK 57 docs. The fastest-rotting material here: Expo Go support (changed at SDK 53), foreground presentation defaults (changing at SDK 58), Firebase console navigation, Apple Developer portal navigation, and EAS CLI prompt wording. Re-verify at [docs.expo.dev/push-notifications/push-notifications-setup](https://docs.expo.dev/push-notifications/push-notifications-setup/) before debugging against this file.

## Packages

```sh
pnpm expo install expo-notifications expo-constants
pnpm expo install expo-task-manager   # only if you need background/headless notifications
```

`expo-device` is optional; push works on physical devices, Android emulators with Play services, and iOS simulators on Xcode 14+ (macOS 13+, iOS 16+), so a hard `Device.isDevice` gate now blocks a valid test target.

## App config

```json
{
  "expo": {
    "plugins": [
      ["expo-notifications", {
        "icon": "./assets/notification-icon.png",
        "color": "#0B0B0F",
        "defaultChannel": "default",
        "sounds": ["./assets/chime.wav"],
        "enableBackgroundRemoteNotifications": false
      }]
    ],
    "android": { "googleServicesFile": "./google-services.json" }
  }
}
```

All five are build-time. Changing any of them requires a new binary — an OTA update will not apply them.

| Field | Requirement | Symptom when wrong |
|---|---|---|
| `icon` | 96×96 PNG, **all white on transparent** | Grey or white square in the Android tray. Enforced by Google, not Expo |
| `color` | Tint applied to that icon | Icon renders in the wrong accent; cosmetic only |
| `defaultChannel` | Channel for FCM v1 sends with no `channelId` | Without it Expo creates a user-facing "Miscellaneous" channel you cannot fully delete |
| `sounds` | `.wav`, referenced later by **base filename only** | Silent notification; passing a path instead of `chime.wav` fails silently |
| `enableBackgroundRemoteNotifications` | Adds `remote-notification` to `UIBackgroundModes` | Headless/background notifications never run the JS task on iOS |

The `notification` field was **removed from app.json in SDK 55** — if you find one, migrate it into the plugin config. The iOS `aps-environment` entitlement is always written as `development`; Xcode rewrites it to `production` in a release archive. Do not "fix" it ([Expo notifications SDK reference](https://docs.expo.dev/versions/latest/sdk/notifications/)).

## The Expo Go trap

Remote push **throws on Android from SDK 53** and is unavailable on iOS ([expo-notifications](https://docs.expo.dev/versions/latest/sdk/notifications/)). Local notifications still work in Expo Go, so a developer schedules one, sees it appear, and concludes the setup is sound. *Symptom: "push works locally, nothing arrives from the server."* Every push test needs a development build.

## Android credentials, end to end

1. Create a Firebase project (or reuse one) at [console.firebase.google.com](https://console.firebase.google.com).
2. **Project settings → Service accounts → Generate new private key.** Save the JSON. Gitignore it — it is a live credential.
3. Upload it to EAS: `eas credentials` → Android → production → Google Service Account → *Manage your Google Service Account Key for Push Notifications (FCM V1)* → upload. Or EAS dashboard → Credentials → Android application identifier → **Service Credentials → FCM V1 service account key**.
4. Download **google-services.json** from Firebase, commit it (it holds public identifiers only), and point `android.googleServicesFile` at it.
5. Rebuild. `google-services.json` is compiled into the binary.

Reusing an existing service account instead of generating one: grant it the **Firebase Cloud Messaging API Admin** role in [IAM](https://console.cloud.google.com/iam-admin/iam) first ([FCM credentials guide](https://docs.expo.dev/push-notifications/fcm-credentials/)).

| Mistake | Symptom |
|---|---|
| Service account key uploaded, `google-services.json` missing or stale | Receipt error `MismatchSenderId`. The `project_number` in the JSON must match the Firebase project the key came from |
| Key revoked or from a deleted project | Receipt error `InvalidCredentials` |
| `google-services.json` API key restricted in Google Cloud | App never gets a token at all. Allow **FCM Registration API** and **Firebase Installations API**, and set Application restrictions to the **app signing certificate SHA-1** from Play Console → Release → Setup → App Integrity, *not* your upload key. Otherwise Firebase Installations returns `403 PERMISSION_DENIED: Requests from this Android client application are blocked` |
| No channel created before requesting the token | `getExpoPushTokenAsync` fails or the Android 13+ permission prompt never appears. `setNotificationChannelAsync` **must** run first |

## iOS credentials, end to end

You need a **paid Apple Developer account**. EAS does the work: on the first `eas build -p ios` it offers to set up push and generate an APNs key. Answer yes to both prompts. Outside a build, `eas credentials`.

**Key, not certificate.** Use the `.p8` APNs authentication key. Certificates are per-app, per-environment, and expire annually; the key is one file for everything. Apple caps you at **two APNs keys per account**, they are **not app-specific**, and they **never expire** — but revoking one breaks push for every app that uses it, and clearing it from EAS does not delete it at Apple. To free a slot you must delete it in the [Apple Developer console](https://developer.apple.com/account/resources/certificates/list) ([app credentials](https://docs.expo.dev/app-signing/app-credentials/)).

Uploading a replacement key does **not** invalidate users' Expo push tokens.

| Mistake | Symptom |
|---|---|
| No push key configured | Build or runtime error: `No valid aps-environment entitlement string found`. Check the project's iOS credentials page |
| `expo-notifications` plugin missing from `plugins` | Same entitlement error — the plugin is what injects `aps-environment` |
| APNs key revoked at Apple | Receipt error `InvalidCredentials`, sometimes with `InvalidProviderToken` in details. That variant is tied to **both** the key and the provisioning profile: regenerate both and rebuild |
| Device has no network / no SIM / firewall blocks port 5223 | `getExpoPushTokenAsync` hangs for a long time. This is Apple, not Expo — see [TN2265](https://developer.apple.com/library/archive/technotes/tn2265/_index.html) |

## Development build vs TestFlight vs production

This is the single most confusing area, because the credentials are identical and the *routing* is not.

| | Development build | TestFlight / Ad Hoc | App Store / Play production |
|---|---|---|---|
| iOS APNs host | Sandbox (`api.sandbox.push.apple.com`) | Production (`api.push.apple.com`) | Production |
| iOS entitlement in binary | `development` | `production` (Xcode rewrites on archive) | `production` |
| Token validity across those | **Not interchangeable** | — | — |
| Android FCM | Same service account and `google-services.json` for all three | Same | Same |
| Expo push token | Same format, tied to `projectId`; Expo routes to the right APNs host per build | Same | Same |

Consequences worth internalising:

- **Symptom: push works in the dev build, silent in TestFlight.** The device is registered against the wrong APNs environment, or you kept a token captured from a dev build. Reinstall the TestFlight build, capture a fresh token, and re-send. Installing a TestFlight build over an Xcode build on the same device sometimes needs a device restart before registration succeeds.
- **Android has no sandbox**, so an Android-only test proves nothing about iOS.
- Store push tokens with the build channel that produced them if you test both on one device; otherwise a stale sandbox token sits in your table producing silent non-delivery rather than an error.

## projectId

Always pass it explicitly. It is what attributes the token to your EAS project, and it survives account renames and project transfers:

```ts
const projectId =
  Constants?.expoConfig?.extra?.eas?.projectId ?? Constants?.easConfig?.projectId;
if (!projectId) throw new Error('Missing EAS projectId');
const token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;
```

*Symptom when omitted in a bare or misconfigured build:* `Project ID not found`, or tokens that resolve but belong to no experience, producing `PUSH_TOO_MANY_EXPERIENCE_IDS` when batched with real ones.

Set `"promptToConfigurePushNotifications": false` under `cli` in **eas.json** so non-interactive CI does not hang on the credentials prompt (`stack-scaffold` covers the rest of eas.json).

## Android channels are mandatory setup, not polish

Since Android 8.0 every notification belongs to a channel; without one Android creates a "Miscellaneous" fallback. Create yours at first launch, before the permission request:

```ts
if (Platform.OS === 'android') {
  await Notifications.setNotificationChannelAsync('reminders', {
    name: 'Reminders',
    importance: Notifications.AndroidImportance.HIGH,   // heads-up + sound
    vibrationPattern: [0, 250, 250, 250],
    lightColor: '#0B0B0F',
  });
  await Notifications.setNotificationChannelAsync('product', {
    name: 'News and offers',
    importance: Notifications.AndroidImportance.DEFAULT, // sound, no heads-up
  });
}
```

Importance maps to visible behaviour: `MAX`/`HIGH` → heads-up with sound; `DEFAULT` → sound only; `LOW` → silent, in the shade; `MIN` → silent, not in the status bar ([Android channels](https://developer.android.com/develop/ui/views/notifications/channels)).

**Channels are immutable after creation.** Only name and description can change; sound, importance and vibration are locked to whatever you shipped first, per install. Re-creating a channel with the same ID is a no-op, so calling this on every launch is safe and correct. Deleting and recreating with new settings does not reset them, and Android displays the count of deleted channels in settings as an anti-spam signal. *Symptom: "I changed importance and nothing happened on my device" — correct behaviour; test on a fresh install.*

Custom sounds need the file in the plugin `sounds` array **and** set on both the channel (Android 8+) and the notification content (below 8).

## Exact alarms and Doze

`expo-notifications` adds `RECEIVE_BOOT_COMPLETED` automatically so scheduled notifications survive a reboot. Exact-time local notifications on Android 12+ need `SCHEDULE_EXACT_ALARM`, and on **Android 14+ that permission is denied by default** for newly installed apps targeting API 33+. `USE_EXACT_ALARM` is granted at install but is **Play-policy restricted to calendar and alarm-clock apps** — declaring it in a habit tracker is a listing rejection ([Android 14 changes](https://developer.android.com/about/versions/14/changes/schedule-exact-alarms)).

Design for inexact. A daily reminder does not need exact alarms; a delivery window of a few minutes is fine and is what the platform wants. Doze defers normal-priority delivery on idle devices regardless — see `sending.md` for the `priority` and `ttl` fields that mitigate it.

## Verification sequence

Run in this order; each step isolates one layer.

1. **Local notification** with `trigger: null` in a dev build. Fails → client code or handler.
2. **Token acquisition.** Log the `ExponentPushToken[...]`. Fails → credentials or channel.
3. **[Expo push tool](https://expo.dev/notifications)** with that token. Fails → credentials.
4. **curl the send endpoint**, capture the ticket ID, then `POST /--/api/v2/push/getReceipts` 15 minutes later. The receipt names the actual fault.
5. Repeat 2–4 on a **TestFlight/internal-track build**, on a device that has never had a dev build installed.
6. Confirm `store-submission`'s checklist line: registration succeeds on a production APNs build and on FCM.

Known SDK 57 issue: launching an **Android debug build** from a notification breaks the splash screen roughly 70% of the time (missing icon, no fade). Release builds are unaffected — test with `npx expo run:android --variant release` before filing a bug.
