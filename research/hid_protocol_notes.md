# HID protocol research — 2026-10-30

Historical protocol notes. For current G3M support see [G3M follow-up](g3m-protocol-2026-10-30.md).

Read-only research and `hid.enumerate()` only. No HID handles opened; no descriptor, feature, input, output, or write report calls were made. Local environment: `hidapi` package/runtime 0.15.0; Python wrapper exposes `get_report_descriptor` and `get_feature_report`.

## ROG Delta II: verified upstream, not live-tested here

Primary source pinned to commit `bd5b36748b2e31aab10e8800f52959e785ccb476`:

- [Protocol](https://github.com/measureer/ROGDeltaTray/blob/bd5b36748b2e31aab10e8800f52959e785ccb476/docs/protocol.md)
- [Query/parser implementation](https://github.com/measureer/ROGDeltaTray/blob/bd5b36748b2e31aab10e8800f52959e785ccb476/src/RogBatteryTray/Hid/HidBatterySource.cs)
- [Device allowlist](https://github.com/measureer/ROGDeltaTray/blob/bd5b36748b2e31aab10e8800f52959e785ccb476/src/RogBatteryTray/Hid/SupportedDevices.cs)
- [MIT license, Copyright (c) 2026 clz](https://github.com/measureer/ROGDeltaTray/blob/bd5b36748b2e31aab10e8800f52959e785ccb476/LICENSE); verbatim local copy: `ROGDeltaTray-LICENSE.txt`. Preserve the full notice when adapting substantial upstream code.

Device: ASUS VID `0B05`, PID `1AFA` (Delta II, upstream hardware-verified). PID `1AD3` Cetra SpeedNova is explicitly unverified upstream; do not claim live support. Delta II's documented USB interface is MI_03, collection COL04, usage page `FF00`. Select by VID/PID and descriptor/caps (vendor page FF00, output length at least 64), not merely the Windows COL04 suffix. Bluetooth mode is outside this USB receiver protocol.

Query transport is **interrupt output write, then interrupt input read**; it is not a GetFeature/SetFeature protocol. Each request is exactly 64 bytes including report ID:

| Request | Bytes | Response field (all indices zero-based) |
|---|---|---|
| Battery | `CC 12 07` + 61 zero bytes | `[6]` = percentage |
| Charging | `CC 12 08` + 61 zero bytes | `[5] == 1` = charging, `[5] == 0` = not charging |

Battery response documented as `CC 12 07 00 00 05 <percent> <threshold> 01 00 ...`. `[5]` is sleep timeout, `[7]` low battery threshold, `[8]` low battery voice prompt — none is the charging flag.

Validation and state handling:

1. Drain stale input with bounded nonblocking/tiny-timeout reads before EACH request (upstream cap 32). Serialize queries per handle. Upstream reads at most four response reports per query with 2-second read/write timeout; retries an ambiguous battery-query failure up to three times with 300 ms between attempts.
2. Header minimum is 3 bytes: `[0] == CC`; expected command echo is EXACTLY `[1:3] == bytes([0x12, command])`, i.e. indices 1 and 2. Skip asynchronous reports with a different echo; do not parse unrelated events as query answers.
3. Header NAK: `[0] == CC` and `[1:3] == FF AA` (minimum 3 bytes). Payload NAK: correct CC/command echo and `[5:7] == FF AA` (minimum 7 bytes). A battery-query NAK is the upstream definitive headset-off signal; distinguish receiver-present/headset-off from receiver-unplugged. Timeout/error is ambiguous and is not a valid percentage.
4. Battery's semantic minimum is 7 bytes to read `[6]`. Charging's semantic minimum is 6 bytes to read `[5]`; payload-NAK checks require 7. The documented normal report is 64 bytes; never pad a short received report and then pretend its zero-filled fields were received. Requiring at least 7 for both query types is a simple stricter policy. Validate charging state in `{0,1}`, otherwise keep it unknown; charge-query failure must not invalidate a good percentage or fabricate `False`.
5. **Our chosen percentage policy:** accept a verified `0..100` value, including genuine `0%`, per the protocol document. Never use `0` alone as disconnected and never clamp `101..255`. Upstream implementation currently rejects `<=0`, conflicting with its documented `0..100` range. Its buffer is 64 bytes but it only checks actual read `n >= 3` before accessing offsets 5/6; do not copy that short-read weakness.

## Edifier / HECATE G3M PRO: no verified protocol yet

The [manufacturer manual](https://edifier.com.my/wp-content/uploads/2024/06/G3M-PRO-User-Manual.pdf) identifies model EDF702003, HECATE Connect configuration software and wired/2.4GHz/Bluetooth modes. It does not document HID VID/PID, feature report IDs, battery offsets, or a battery command. The search-indexed manual text was accessible; opening the PDF returned HTTP 403. No verified G3M PRO HID battery protocol was found in the consulted primary sources. Do not reuse the ASUS command on it, and do not equate MCHOSE G3 V2 with G3M PRO.

Safe diagnostic design for when the actual device is connected:

1. Enumerate; positively identify exact model/VID/PID/interface. Read its report descriptor/caps first, using a diagnostic mode restricted to that device. Stop if target is absent or ambiguous.
2. Derive **declared feature report IDs and lengths** from the descriptor/caps, then use only `get_feature_report(id, length)` for a bounded read-only sample. ID is the first returned byte; data follows it. No blind scan over IDs, guessed battery offsets, `write`, `send_feature_report`, SetFeature, output report, firmware, pairing, LED, DPI, or reset commands.
3. Exclude unrelated keyboard/mouse collections. If there are no declared feature reports, report that limitation and stop rather than inventing an initialization write. A vendor-defined report with arbitrary 0..100 bytes is insufficient evidence for battery/charging. Keep status unknown until a documented standard usage or a verified protocol plus repeated ground-truth samples establishes it.

Primary API documentation: [HIDAPI GetFeature and descriptor API](https://libusb.info/hidapi/group__API.html), [Windows HidD_GetFeature](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/hidsdi/nf-hidsdi-hidd_getfeature), [HIDP_CAPS](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/hidpi/ns-hidpi-_hidp_caps). Windows FeatureReportByteLength includes the report-ID byte; ID 0 means unnumbered report. GET_FEATURE returns data; it supplies no arbitrary command payload. Protocol-specific side effects cannot be guaranteed by the generic API alone.
