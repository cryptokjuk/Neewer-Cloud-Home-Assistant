# Neewer Cloud for Home Assistant

Control Neewer smart lights through Neewer's cloud — the same path the
**NEEWER Home** app uses — instead of Bluetooth.

This exists because some Neewer models (for example the **NR01** outdoor string
lights) expose no local network API at all: the Wi-Fi radio only talks to
Neewer's servers. Cloud control also survives when local Bluetooth cannot get a
connection.

## Features

- Sign in with your NEEWER Home account (email or phone + password).
- One light entity per device on the account.
- Power, brightness, colour temperature and RGB colour.
- The full scene/theme catalogue as Home Assistant **effects**, fetched live
  from Neewer's cloud, including device-specific themes.
- `cloud_last_error` attribute for troubleshooting.

## Requirements

- Home Assistant 2024.1 or newer.
- A Neewer Home account with at least one device.
- The device must be **online in Neewer's cloud** (Wi-Fi connected). Cloud
  control does not work while the device is offline.
- Internet access.

## Installation

### HACS (custom repository)

1. HACS → three dots → **Custom repositories**.
2. Add this repository's URL, category **Integration**.
3. Install **Neewer Cloud**.
4. Restart Home Assistant.

### Manual

Copy `custom_components/neewer_cloud` into your Home Assistant
`config/custom_components/` directory and restart.

## Configuration

1. Settings → Devices & Services → **Add Integration**.
2. Search for **Neewer Cloud**.
3. Enter your NEEWER Home account and password.

No device IP addresses are needed: the integration discovers your devices from
the account.

## Notes and limitations

- **Private API.** This was reconstructed from the NEEWER Home Android app.
  Neewer can change it at any time, which would break the integration until it
  is updated.
- **Credentials.** The account password is stored in the Home Assistant config
  entry (Home Assistant does not encrypt these). Use a unique password, and
  remove the integration if you stop using it.
- **Cloud dependency.** Commands go through Neewer's servers, so they need
  internet and add some latency. There is no local fallback in this integration.
- **State is optimistic.** There is no documented status endpoint; the entity
  reflects the last command rather than the device's confirmed state.
- Scene names come from Neewer's catalogue and may differ slightly in case or
  wording from the app (for example `Christmas tree`). Effect names match
  case-insensitively, so both spellings work.

## Troubleshooting

| Symptom | Meaning |
|---|---|
| `20015: the device is offline` | The device is not connected to Neewer's cloud. Check its Wi-Fi and power; the NEEWER Home app will show the same state. |
| `invalid_auth` during setup | Wrong account or password. |
| `cannot_connect` during setup | Neewer's cloud could not be reached. |

The `cloud_last_error` attribute on the light entity shows the last API error.

## Disclaimer

Unofficial. Not affiliated with, endorsed by, or supported by Neewer. The
Neewer name and logo are trademarks of their owner and are used only to
identify the hardware this integration talks to. The brand image is Neewer's
public site logo.
