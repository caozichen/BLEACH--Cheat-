import sys
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '分析依赖'))
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN

RAM = (ROOT / 'stage-RAM.dump').read_bytes()
BASE = 0x08800000
MD = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
MD.skipdata = True

def disasm(start, end):
    for ins in MD.disasm(RAM[start-BASE:end-BASE], start):
        print(f'{ins.address:08X}  {ins.bytes.hex():8s}  {ins.mnemonic:10s} {ins.op_str}')

def scan():
    interesting = {0x798, 0x7a4, 0x234, 0x240, 0x8f0, 0x3b4, 0x3b5, 0x3b6, 0x3b7,
                   0x3b8, 0x3b9, 0xb18, 0xb19, 0xb1a, 0xb1b, 0xb1c, 0xb1d, 0x270f}
    hits = {}
    for offset in range(0x4000, 0x1e0000, 4):
        word = struct.unpack_from('<I', RAM, offset)[0]
        imm = word & 0xffff
        op = word >> 26
        if imm not in interesting or op not in {8, 9, 10, 11, 12, 13, 14, 32, 33, 35, 36, 37, 40, 41, 43, 49, 57}:
            continue
        hits.setdefault(imm, []).append(BASE + offset)
    for imm, addresses in sorted(hits.items()):
        print(f'OFFSET {imm:04X}: ' + ', '.join(f'{a:08X}' for a in addresses))
    for address in [0x08d06524 + 0x798, 0x08d06524 + 0x8f0, 0x08d06a88 + 0x3b4]:
        print(f'DATA {address:08X}:', RAM[address-BASE:address-BASE+48].hex(' '))

if len(sys.argv) > 1:
    disasm(int(sys.argv[1], 16), int(sys.argv[2], 16))
else:
    scan()
