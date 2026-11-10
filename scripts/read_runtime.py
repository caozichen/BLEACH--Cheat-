"""Read PPSSPP actor values through read-only Windows process APIs."""
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', required=True, type=int, help='Isolated PPSSPPWindows64.exe process ID')
    parser.add_argument('--snapshot', type=Path, default=ROOT / 'materials/ram/stage-RAM.dump')
    parser.add_argument('--output', type=Path, default=ROOT / 'work/runtime-validation.json')
    parser.add_argument('--expect-multiplier', type=int, choices=[1, 16, 32, 64])
    parser.add_argument('--expect-hp', type=int)
    parser.add_argument('--expect-defense', type=int)
    args = parser.parse_args()
    if sys.platform != 'win32':
        parser.error('Live process inspection requires Windows.')
    if ctypes.sizeof(ctypes.c_void_p) != 8:
        parser.error('Use 64-bit Python to inspect PPSSPPWindows64.exe.')
    snapshot = args.snapshot.read_bytes()
    if len(snapshot) != 0x1800000:
        parser.error('Snapshot must be a 24 MiB PSP RAM export starting at 0x08800000.')
    offset = 0x33d70
    signature = snapshot[offset:offset + 64]
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)

    class MBI(ctypes.Structure):
        _fields_ = [('BaseAddress', ctypes.c_void_p), ('AllocationBase', ctypes.c_void_p),
                    ('AllocationProtect', wintypes.DWORD), ('PartitionId', wintypes.WORD),
                    ('RegionSize', ctypes.c_size_t), ('State', wintypes.DWORD),
                    ('Protect', wintypes.DWORD), ('Type', wintypes.DWORD)]

    k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                    ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    k32.VirtualQueryEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.POINTER(MBI), ctypes.c_size_t]
    k32.VirtualQueryEx.restype = ctypes.c_size_t
    k32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                            ctypes.POINTER(wintypes.DWORD)]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = k32.OpenProcess(0x0410, False, args.pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())

    def read(address, size):
        buf = ctypes.create_string_buffer(size)
        got = ctypes.c_size_t()
        ok = k32.ReadProcessMemory(handle, address, buf, size, ctypes.byref(got))
        return buf.raw if ok and got.value == size else None

    try:
        exe = ctypes.create_unicode_buffer(32768)
        exe_size = wintypes.DWORD(len(exe))
        if not k32.QueryFullProcessImageNameW(handle, 0, exe, ctypes.byref(exe_size)):
            raise ctypes.WinError(ctypes.get_last_error())
        if Path(exe.value).name.lower() != 'ppssppwindows64.exe':
            raise ValueError('PID does not belong to PPSSPPWindows64.exe.')
        regions = []
        address = 0
        while address < 0x7fffffffffff:
            region = MBI()
            if not k32.VirtualQueryEx(handle, address, ctypes.byref(region), ctypes.sizeof(region)):
                break
            base = region.BaseAddress or 0
            size = region.RegionSize
            if region.State == 0x1000 and not region.Protect & 0x101 and size >= 0x1800000:
                for prefix in (0x800000, 0):
                    if prefix + offset + 64 <= size and read(base + prefix + offset, 64) == signature:
                        regions.append(base + prefix)
            if not size or base + size <= address:
                break
            address = base + size
        if not regions:
            raise ValueError('Game-code signature was not found; verify game version and snapshot.')
        host = regions[0]

        def u32(psp):
            if not 0x08800000 <= psp <= 0x09fffffc:
                raise ValueError(f'PSP address outside RAM: {psp:#x}')
            raw = read(host + psp - 0x08800000, 4)
            if raw is None:
                raise ValueError(f'Could not read PSP address {psp:#x}.')
            return struct.unpack('<I', raw)[0]

        player = u32(0x08f1d46c)
        if not 0x08800000 <= player <= 0x09fff000:
            raise ValueError('Player pointer is not valid; enter a controllable stage first.')
        result = {'pid': args.pid, 'matchedRamViews': len(regions), 'playerPointer': hex(player),
                  'attackBonuses': [u32(player + off) for off in (0x918, 0x91c, 0x920, 0x924, 0x928, 0x92c)],
                  'hp': u32(player + 0x798), 'maxHp': u32(player + 0x8e8),
                  'defense': u32(player + 0x8f4), 'sp': u32(player + 0x7a4) & 0xffff}
        checks = {}
        if args.expect_multiplier is not None:
            checks['attack'] = result['attackBonuses'] == [(args.expect_multiplier - 1) * 100] * 6
        if args.expect_hp is not None:
            checks['hpAndMaxHp'] = result['hp'] == result['maxHp'] == args.expect_hp
        if args.expect_defense is not None:
            checks['defense'] = result['defense'] == args.expect_defense
        result['checks'] = checks
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result, indent=2))
        return 0 if all(checks.values()) else 1
    finally:
        k32.CloseHandle(handle)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        raise SystemExit(str(exc))
