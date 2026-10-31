# G3M PRO protocol follow-up — 2026-10-30

Protocol reference with pinned upstream sources and license notices.

## Supported device and transport

Supported manufacturer `Telink`, product `G3M PRO`, VID:PID `320F:706E`, interface 1, vendor usage page `FF1C`, usage `0092`.

Descriptor: `061cff0992a1018504190029ff150026ff007508953f8100190029ff150026ff007508953f9100c0`.

It declares report ID 4 with 63 data bytes for input and output (64 bytes including ID), and no Feature reports. Therefore GET_FEATURE cannot implement this vendor battery query. This is an exact match to the upstream Python protocol's manufacturer/product/VID/PID and channel.

- [Nefeli0721 Python implementation, pinned](https://github.com/Nefeli0721/g3m-battery/blob/354c4ca0b861b411c86995617030e29ed3ffddc6/g3m_battery.py)
- [Static analysis and dynamic cross-check, pinned](https://github.com/Nefeli0721/g3m-battery/blob/354c4ca0b861b411c86995617030e29ed3ffddc6/docs/findings-static.md)
- [Upstream readme, pinned](https://github.com/Nefeli0721/g3m-battery/blob/354c4ca0b861b411c86995617030e29ed3ffddc6/README.md)

Upstream identifies `MI_01&COL04`, but select by actual numeric VID/PID/interface/usage and descriptor rather than trusting a COL suffix or manufacturer containing EDIFIER/HECATE. A different primary implementation lists wired alias `320F:706B` with the same vendor usage and 64-byte reports; that alias was not locally observed by this researcher: [Go Windows HID implementation](https://github.com/Sanjeever/g3m-battery/blob/5d94130852b1e68e7cf28fbc2e706f81c92195a0/cmd/g3m-battery/hid_windows.go). Do not treat all devices sharing Telink/VID320F as this mouse.

## Documented battery-only query

Transport is 64-byte **interrupt output write, then input read** on the exact vendor collection. No SetFeature, configuration session, profile read/write, DPI, LED, pairing, reset, or firmware command is needed. Direct battery query is explicitly implemented and independently verified in upstream sources.

Request bytes:

```text
04 20 00 1A 06 00 00 00 + 56 zero bytes
```

All indices zero-based:

| Offset | Request meaning |
|---|---|
| 0 | HID Report ID `04` |
| 1..2 | Little-endian sum of request bytes 3..63; here `0020` |
| 3 | Command `1A`: read status block |
| 4 | Requested data length `06`; this is a length, not a second opcode |
| 5..6 | Little-endian offset `0000` |
| 7 | Reserved zero |
| 8..63 | Zero |

Do not prepend an extra report-ID byte when using hidapi: the first `04` already is the report ID.

Optional upstream readiness query, only if needed: `04 AA 00 AA 00 00 00 00` + 56 zeros; normal matching response `[0]=04,[3]=AA,[7]=00,[8]=FF`. The static analysis calls this “get 2.4G mode”; use it only as the documented readiness probe, not as proof of a percentage. No need to begin/end a configuration session for direct battery polling.

### Response and validation

Upstream hardware example: official UI at 90% matched response prefix `04 20 00 1A 06 00 00 00 5A`. The readme's JSON example has six-byte data `5a0100000000`. Static report says unused bytes after offset 13 are zero. Combining those documented fields gives the following *illustrative assembled 64-byte response*, not a local capture:

```text
04 20 00 1A 06 00 00 00 5A 01 00 00 00 00 + 50 zero bytes
```

| Field | Rule |
|---|---|
| Actual read length | Require the declared 64 bytes for this application; never pad a short input and treat synthesized zeros as device data |
| `[0]` | Must be `04` |
| `[3]` | Must echo `1A`; skip unrelated reports within a bounded deadline |
| `[7]` | Normal `00`; `FF` means error -102 and `FE` error -103; keep unknown for other undocumented status values |
| `[8]` | Direct integer percentage, `0..100`, including genuine zero; reject >100 |
| `[9]` | Raw charge flag; see conflicting evidence below |
| `[10..13]` | Other status bytes, semantics not established for this mouse |

Response `[1..2]` **echoes the request checksum**, it is not a sum recomputed over the response containing data. Do not reject valid responses because their payload changes that sum. Known battery response header echo is `04 20 00 1A 06 00 00 00`. The static evidence's primary semantic checks are matching command and status; no source here proves every firmware must preserve every other reserved header byte.

Bound stale-input draining (e.g. max 16 reports), serialize transactions per handle, bound read attempts/deadline, run all HID calls in a killable worker so UI cannot hang, and publish fresh confirmed state only. Receiver absence, timeout/possible mouse sleep, and malformed report are different from a valid 0% reading. Nefeli's implementation clamps >100 and has an unnecessary 15-byte minimum; do not copy either behavior. Stronger 64-byte framing is justified by actual descriptor and device protocol.

### Ground truth and charging uncertainty

Nefeli's sources report three evidence types: passive observations while official HECATE UI showed 90%; static analysis of official software; independent reads after the official process was terminated. The readme additionally reports plugging/unplugging charging cable switches `[9]` between 0 and 1, and 100%-while-connected stayed at raw 1 in 111 samples over six minutes. Its mapping is 0=discharge, 1=charging, 2=full, though raw2 was never seen on that author's device. Treat its 100%+flag1 “full” label as a UI convention rather than a distinct measured device flag.

A different primary implementation uses 2=charging and interprets 1 only when wired, leaving receiver+1 unknown: [Go charge decoder](https://github.com/Sanjeever/g3m-battery/blob/5d94130852b1e68e7cf28fbc2e706f81c92195a0/cmd/g3m-battery/battery_state_windows.go). [Windows C# implementation](https://github.com/BlueEve04/G3M-PRO-Controller/blob/38a11b1bfcb32506f1c2951a33a9e6aaa1723033/src/G3M.Core/Model/BatteryState.cs) copies that Go mapping; it is not independent evidence resolving the conflict.

Thus **percentage protocol is corroborated; nonzero charging interpretation is inconsistent across primary implementations**. Preserve raw flag in diagnostics, keep charging unknown until this exact device has suitable cable/ground-truth validation, and do not claim raw2 means “full” or “charging” solely from a different firmware's mapping.

## Independent protocol corroboration

- [BoBppy macOS C bridge](https://github.com/BoBppy/g3mpro-macos/blob/6271ac2bfc482168d88e95480a8bcc5c05a16ff5/Sources/CHIDBridge/CHIDBridge.c): same VID/PID/interface/usage, same packet builder, same `1A,length6,offset0`, percent `[8]`. It performs larger configuration snapshots within sessions; battery-only polling need not copy those extra transactions.
- [Windows direct battery controller](https://github.com/BlueEve04/G3M-PRO-Controller/blob/38a11b1bfcb32506f1c2951a33a9e6aaa1723033/src/G3M.Core/Services/G3mController.cs): `ReadBatteryOnce` directly queries battery without session/ping.
- [Windows packet format](https://github.com/BlueEve04/G3M-PRO-Controller/blob/38a11b1bfcb32506f1c2951a33a9e6aaa1723033/src/G3M.Core/Protocol/G3mPacket.cs): same report layout.
- EZ2.4G and 2.4G-battery-viewer repository metadata/tree were inspected, but the exact G3M projects above provide better evidence. No generic “any 0..100 byte is battery” heuristic is warranted.

## Reuse/license notice

Nefeli Python source is MIT: [pinned LICENSE](https://github.com/Nefeli0721/g3m-battery/blob/354c4ca0b861b411c86995617030e29ed3ffddc6/LICENSE). Preserve the notice below if adapting substantial implementation. Protocol facts alone are distinguished from copying source code. macOS source is MIT Copyright (c) 2026 BoBppy; [pinned license](https://github.com/BoBppy/g3mpro-macos/blob/6271ac2bfc482168d88e95480a8bcc5c05a16ff5/LICENSE). Go source is MIT Copyright (c) 2026 Sanjeever; [pinned license](https://github.com/Sanjeever/g3m-battery/blob/5d94130852b1e68e7cf28fbc2e706f81c92195a0/LICENSE). The C# README says MIT, but no standalone LICENSE exists in its inspected tree, so prefer clearly licensed Python/macOS sources for copied implementation.

### Nefeli0721/g3m-battery full MIT notice

```text
MIT License

Copyright (c) 2026 G3M Battery contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

