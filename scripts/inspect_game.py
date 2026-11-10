"""Disassemble a local 24 MiB UCAS40234 PSP RAM snapshot using Capstone."""
import argparse
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, default=ROOT / 'materials/ram/stage-RAM.dump')
    parser.add_argument('--start', type=lambda s: int(s, 16))
    parser.add_argument('--end', type=lambda s: int(s, 16))
    parser.add_argument('--scan', action='store_true', help='Scan instructions for known actor-field offsets')
    args = parser.parse_args()
    ram = args.snapshot.read_bytes()
    if len(ram) != 0x1800000:
        parser.error('Expected a 24 MiB RAM export starting at 0x08800000.')
    base = 0x08800000
    if args.scan:
        interesting = {0x798, 0x7a4, 0x7dc, 0x8e8, 0x8f0, 0x8f4, 0x918, 0x91c, 0x920,
                       0x924, 0x928, 0x92c, 0x934, 0x938, 0x93c, 0x270f}
        hits = {}
        for offset in range(0x4000, 0x1e0000, 4):
            word = struct.unpack_from('<I', ram, offset)[0]
            imm = word & 0xffff
            op = word >> 26
            if imm in interesting and op in {8, 9, 10, 11, 12, 13, 14, 32, 33, 35, 36, 37, 40, 41, 43, 49, 57}:
                hits.setdefault(imm, []).append(base + offset)
        for imm, addresses in sorted(hits.items()):
            print(f'OFFSET {imm:04X}: ' + ', '.join(f'{a:08X}' for a in addresses))
    else:
        if args.start is None or args.end is None or not base <= args.start < args.end <= base + len(ram):
            parser.error('Provide --scan or a valid --start and --end RAM address.')
        try:
            from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
        except ImportError:
            parser.error('Install requirements-analysis.txt before disassembling.')
        decoder = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
        decoder.skipdata = True
        for ins in decoder.disasm(ram[args.start - base:args.end - base], args.start):
            print(f'{ins.address:08X}  {ins.bytes.hex():8s}  {ins.mnemonic:10s} {ins.op_str}')


if __name__ == '__main__':
    main()
