"""Derive one presentation state without interfering with user animation input."""


def derive_state(snapshots):
    for name in ('rog','g3m'):
        source = snapshots.get(name,{})
        percent = source.get('percent')
        if source.get('status') == 'ok' and type(percent) is int and percent <= 20 and not source.get('charging'):
            return 'low_battery'
    if any(source.get('status') == 'error' for source in snapshots.values()):
        return 'error'
    dsh = snapshots.get('dsh',{})
    if dsh.get('running') and dsh.get('activity') in ('working','tool','retrying','approval'):
        return 'working'
    return 'idle'
