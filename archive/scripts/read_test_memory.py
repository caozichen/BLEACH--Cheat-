"""Read only the isolated PPSSPP test process; never writes process memory."""
import ctypes
import json
import struct
from pathlib import Path
from ctypes import wintypes

ROOT = Path(__file__).resolve().parent
pid = int((ROOT / 'attack-test-pid.txt').read_text(encoding='utf-8-sig').strip())
k32 = ctypes.WinDLL('kernel32', use_last_error=True)

class MBI(ctypes.Structure):
    _fields_ = [('BaseAddress', ctypes.c_void_p), ('AllocationBase', ctypes.c_void_p),
                ('AllocationProtect', wintypes.DWORD), ('PartitionId', wintypes.WORD),
                ('RegionSize', ctypes.c_size_t), ('State', wintypes.DWORD),
                ('Protect', wintypes.DWORD), ('Type', wintypes.DWORD)]

k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
k32.OpenProcess.restype = wintypes.HANDLE
k32.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.VirtualQueryEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.POINTER(MBI), ctypes.c_size_t]
k32.VirtualQueryEx.restype = ctypes.c_size_t
k32.CloseHandle.argtypes = [wintypes.HANDLE]
handle = k32.OpenProcess(0x0410, False, pid)
if not handle:
    raise ctypes.WinError(ctypes.get_last_error())

def read(address, size):
    buf = ctypes.create_string_buffer(size)
    got = ctypes.c_size_t()
    if not k32.ReadProcessMemory(handle, address, buf, size, ctypes.byref(got)):
        return None
    return buf.raw[:got.value]

snapshot = (ROOT / 'stage-RAM.dump').read_bytes()
signature_offset = 0x33d70
signature = snapshot[signature_offset:signature_offset + 64]
regions = []
address = 0
try:
    while address < 0x7fffffffffff:
        region = MBI()
        if not k32.VirtualQueryEx(handle, address, ctypes.byref(region), ctypes.sizeof(region)):
            break
        base = region.BaseAddress or 0
        size = region.RegionSize
        if region.State == 0x1000 and not region.Protect & 0x101 and size >= 0x1800000:
            for prefix in (0x800000, 0):
                if prefix + signature_offset + 64 > size:
                    continue
                match = read(base + prefix + signature_offset, 64)
                if match == signature:
                    regions.append((base + prefix, size, region.Type))
        if not size or base + size <= address:
            break
        address = base + size
    if not regions:
        raise RuntimeError('Could not identify PSP RAM by game-code signature')
    host, size, kind = regions[0]
    def u32(psp):
        raw = read(host + psp - 0x08800000, 4)
        return struct.unpack('<I', raw)[0] if raw else None
    player = u32(0x08f1d46c)
    result = {'pid': pid, 'matchedRamViews': len(regions), 'hostRamAddress': hex(host),
              'playerPointer': hex(player),
              'attackBonuses': [u32(player+off) for off in (0x918,0x91c,0x920,0x924,0x928,0x92c)],
              'hp': u32(player+0x798), 'maxHp': u32(player+0x8e8),
              'defense': u32(player+0x8f4),
              'sp': u32(player+0x7a4) & 0xffff}
    result['attack32xVerified'] = result['attackBonuses'] == [3100] * 6
    (ROOT / 'attack-runtime-validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
finally:
    k32.CloseHandle(handle)
