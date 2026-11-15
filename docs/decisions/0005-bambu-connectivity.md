<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# 0005 — Bambu printer connection

**Status:** Accepted for LAN (phase 2). Cloud sending rejected for now. Firmware work: not
started and will not be started without asking the owner.

## What exists in the fork

OrcaSlicer talks to Bambu printers through `BBLNetworkPlugin` / `BBLPrinterAgent`
(`src/slic3r/Utils/`), which load Bambu Lab's **closed-source** network plugin library at run
time. That plugin is not part of Slyce and is not covered by our licence. The printer-agent
boundary ([printer-agent.md](../HLSD/printer-agent.md)) lets us add an open agent beside it.

## What the protocol looks like (sources)

Community documentation and clients, all describing the same LAN protocol:

- [Doridian/OpenBambuAPI](https://github.com/Doridian/OpenBambuAPI) — protocol documentation
  (GFDL-1.3; we read it and implement from it, we don't copy its text into code).
- [BambuTools/bambulabs_api](https://github.com/BambuTools/bambulabs_api) (MIT) — Python client.
- [greghesp/ha-bambulab](https://github.com/greghesp/ha-bambulab) (MIT) — Home Assistant client.
- Bambu Lab's own [printer network ports](https://wiki.bambulab.com/en/general/printer-network-ports)
  page.

Summary (to be re-checked against those sources while implementing):
- **MQTT over TLS, port 8883**, user `bblp`, password = printer access code. Reports on
  `device/<serial>/report`, commands on `device/<serial>/request` as JSON with a `sequence_id`;
  `pushall` asks for a full state report.
- **FTPS (implicit TLS), port 990**, same credentials, for uploading the `.gcode.3mf`; a
  `project_file` MQTT command then starts the print.
- **Camera:** model-dependent. X-series use RTSP(S); A1/P1 use a JPEG stream over a TLS socket
  (port 6000 is reported); newer models are reported to use other ports. Verify per model.

## Bambu's authorisation change (honest summary)

- In January 2025 Bambu Lab announced an "Authorization Control" firmware change that requires
  authorised clients for many printer actions and blocked unofficial software (including
  OrcaSlicer) from controlling printers directly
  ([Hackaday](https://hackaday.com/2025/01/17/new-bambu-lab-firmware-update-adds-mandatory-authorization-control-system),
  [Tom's Hardware](https://www.tomshardware.com/3d-printing/bambu-lab-security-update-will-remove-orcaslicers-access),
  [Bambu blog](https://blog.bambulab.com/updates-and-third-party-integration-with-bambu-connect/)).
- Bambu's answer for third-party software is **Bambu Connect** (their app) and a **Developer
  Mode** that works only in **LAN-only mode**, does not require authorisation, and disconnects the
  printer from Bambu Cloud
  ([Bambu wiki: third-party integration](https://wiki.bambulab.com/en/software/third-party-integration)).
  Reports say X1 got it in firmware 01.08.05.00 (March 2025) and A/P series in June 2025
  ([All3DP](https://all3dp.com/4/bambu-labs-controversial-authorization-control-hits-budget-3d-printers/)).
- These sources are from 2025. Bambu's policy may have changed since; re-check current firmware
  notes before shipping phase 2.

## Decision

- Implement an **open LAN agent** (MQTT + FTPS + camera) behind the printer-agent boundary, for
  printers in LAN-only + Developer Mode. Document clearly in the UI that this disconnects the
  printer from Bambu Cloud.
- Keep upstream's Bambu network-plugin path available for users who choose to install Bambu's
  plugin; Slyce does not ship it.
- **Cloud sending: not implemented.** Doing it without Bambu's authorisation would mean
  extracting or impersonating Bambu's client credentials, which conflicts with their terms and
  with the brief's security rule. Revisit only if Bambu publishes an official third-party API.
- **Firmware reverse engineering / custom firmware: not started; will ask the owner first.**
