"""G3M Pro verified read-only battery query; bounded diagnostic for unknown devices.

Protocol source/notice: research/g3m-protocol-2026-10-30.md. No configuration writes.
Every HID call runs in a worker with a hard timeout.
"""
import re
import time
from pathlib import Path
from sources.config import write_json


def is_candidate(device):
    product = (device.get('product_string') or '').upper()
    brand = ((device.get('manufacturer_string') or '')+' '+product).upper()
    return is_known_device(device) or bool(re.search(r'\bG3M[ _-]*PRO\b', product) and
                ('EDIFIER' in brand or 'HECATE' in brand) and device.get('usage_page',0) >= 0xFF00)


def is_known_device(device):
    return (device.get('vendor_id')==0x320F and device.get('product_id')==0x706E and
            device.get('interface_number')==1 and device.get('usage_page')==0xFF1C and
            device.get('usage')==0x92 and 'G3M' in (device.get('product_string') or '').upper())


def battery_packet():
    # Report ID4, checksum0x20, ReadBattery1A, six payload bytes, offset0.
    return bytes.fromhex('04 20 00 1A 06 00 00 00')+bytes(56)


def parse_battery(report):
    if len(report)!=64 or bytes(report[:8])!=bytes.fromhex('04 20 00 1A 06 00 00 00'):
        return None
    if not 0<=report[8]<=100:
        return None
    # Sources disagree on nonzero charging flags; do not guess a charge state.
    return dict(percent=int(report[8]),charging=False if report[9]==0 else None)


def query_battery(device):
    for _ in range(16):
        if not device.read(64,1): break
    if device.write(battery_packet())!=64:
        return None
    deadline=time.monotonic()+1.25
    for _ in range(10):
        if time.monotonic()>=deadline: break
        report=device.read(64,150)
        value=parse_battery(report)
        if value is not None:
            return value
    return None


def feature_reports(descriptor):
    """Parse HID global size/count/id and main Feature items, bounded to 256 bytes."""
    reports = {}
    size = count = identifier = 0
    stack = []
    offset = 0
    descriptor = bytes(descriptor)[:4096]
    while offset < len(descriptor):
        prefix = descriptor[offset]
        offset += 1
        if prefix == 0xFE:
            if offset+2 > len(descriptor): break
            length = descriptor[offset]
            offset += 2+length
            continue
        length = (0,1,2,4)[prefix & 3]
        if offset+length > len(descriptor): break
        value = int.from_bytes(descriptor[offset:offset+length],'little')
        offset += length
        kind,tag = (prefix >> 2)&3,prefix >> 4
        if kind == 1:
            if tag == 7: size = value
            elif tag == 8: identifier = value
            elif tag == 9: count = value
            elif tag == 10 and len(stack)<16: stack.append((size,count,identifier))
            elif tag == 11 and stack: size,count,identifier = stack.pop()
        elif kind == 0 and tag == 11 and 0 <= identifier <= 255:
            bits = size*count
            if 0 < bits <= 2040:
                reports[identifier] = reports.get(identifier,0)+bits
    return {key:(bits+7)//8+1 for key,bits in reports.items() if 0<bits<=2040}


def probe_device(device):
    descriptor = bytes(device.get_report_descriptor())[:4096]
    reports = []
    for identifier,length in list(feature_reports(descriptor).items())[:8]:
        try:
            response = bytes(device.get_feature_report(identifier,length))
            reports.append(dict(id=identifier,length=length,received=len(response),hex=response[:256].hex()))
        except OSError:
            reports.append(dict(id=identifier,length=length,code='read_failed'))
    return dict(percent=None, reports=reports, descriptor_hex=descriptor.hex())


def run(config, state_root):
    import hid
    devices = hid.enumerate()
    candidates = sorted([device for device in devices if is_candidate(device)],key=lambda d:not is_known_device(d))
    # Inventory is numeric and excludes serial numbers, raw instance paths and strings.
    diagnostic = dict(devices=[dict(vid=d['vendor_id'],pid=d['product_id'],
        interface=d.get('interface_number'),usage_page=d.get('usage_page'),usage=d.get('usage'))
        for d in devices[:128]], target_found=bool(candidates))
    result = dict(status='unavailable',code='receiver_missing',percent=None,charging=None)
    if candidates:
        device = hid.device()
        try:
            device.open_path(candidates[0]['path'])
            if is_known_device(candidates[0]):
                value=query_battery(device)
                result.update(value or {})
                result.update(status='ok' if value is not None else 'unavailable',
                              code='ready' if value is not None else 'battery_no_response')
                diagnostic['protocol']='g3m-telink-read-battery-1a'
                diagnostic['battery']=value
            else:
                diagnostic['probe'] = probe_device(device)
                result['code'] = 'protocol_unverified'
        finally:
            device.close()
    try:
        write_json(Path(state_root)/'diagnostics/g3m.json',diagnostic)
    except OSError:
        pass
    return result
