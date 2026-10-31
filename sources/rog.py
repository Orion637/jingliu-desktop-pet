"""ROG Delta II known read-only query protocol; see research/hid_protocol_notes.md.

The OUT reports request battery information; no vendor configuration is written.
Only call run() in a killable worker process: even enumeration may block in a HID driver.
"""
import time


def is_candidate(device):
    return (device.get('vendor_id') == 0x0B05 and device.get('product_id') == 0x1AFA
            and device.get('interface_number') == 3 and device.get('usage_page') == 0xFF00)


def valid_response(packet, command):
    return (len(packet) >= 7 and bytes(packet[:3]) == bytes((0xCC, 0x12, command))
            and bytes(packet[5:7]) != b'\xff\xaa')


def parse_battery(packet):
    if valid_response(packet, 7) and 0 <= packet[6] <= 100:
        return int(packet[6])
    return None


def parse_charging(packet):
    if valid_response(packet, 8) and packet[5] in (0, 1):
        return bool(packet[5])
    return None


def query(device, command, parser):
    for _ in range(32):
        if not device.read(64, 1):
            break
    payload = bytes((0xCC, 0x12, command)) + bytes(61)
    if device.write(payload) != 64:
        return None
    deadline = time.monotonic() + .7
    for _ in range(32):
        if time.monotonic() >= deadline:
            break
        value = parser(device.read(64, 80))
        if value is not None:
            return value
    return None


def run(config=None, state_root=None):
    import hid
    devices = [d for d in hid.enumerate(0x0B05, 0x1AFA) if is_candidate(d)]
    if not devices:
        return dict(status='unavailable', code='receiver_missing', percent=None, charging=None)
    device = hid.device()
    try:
        device.open_path(devices[0]['path'])
        percent = query(device, 7, parse_battery)
        charging = query(device, 8, parse_charging) if percent is not None else None
        return dict(status='ok' if percent is not None else 'unavailable',
                    code='ready' if percent is not None else 'headset_offline', percent=percent, charging=charging)
    finally:
        device.close()
