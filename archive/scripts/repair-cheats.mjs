import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));
const source = 'C:/Users/曹梓晨/Documents/PPSSPP/PSP/Cheats/UCAS40234.ini';
const original = await fs.readFile(source);
const text = original.toString('utf8');
const attackOffsets = [0x918, 0x91c, 0x920, 0x924, 0x928, 0x92c];
const hex = n => '0x' + n.toString(16).padStart(8, '0').toUpperCase();
function pointerWrite(offset, value, bits = 32) {
  return `_L 0x6071D46C ${hex(value)}\r\n_L ${bits === 32 ? '0x00020001' : '0x00010001'} ${hex(offset)}\r\n`;
}
function attackBlock(multiplier, enabled) {
  return `_C${enabled ? 1 : 0} 攻击倍率${multiplier}倍_同类仅开一项\r\n` +
    attackOffsets.map(offset => pointerWrite(offset, (multiplier - 1) * 100)).join('');
}

const blocks = text.split(/(?=^_C[0-9])/m);
const index = blocks.findIndex(block => block.includes('0x60000FF8 0x0000FFFF'));
assert(index >= 0, 'Original attack block not found');
assert.match(blocks[index], /0x00020006 0x000003B4/);
blocks[index] = attackBlock(32, true) + '\r\n' + attackBlock(16, false) + '\r\n' + attackBlock(64, false) + '\r\n' + attackBlock(1, false) + '\r\n';
const hpOption = '_C0 锁HP99999_与原锁HP二选一\r\n' + pointerWrite(0x798, 99999) + pointerWrite(0x8e8, 99999);
const defenseOption = '_C0 防御力9999_降低普通物理伤害\r\n' + pointerWrite(0x8f4, 9999);
const candidate = (blocks.join('') + '\r\n' + hpOption + '\r\n' + defenseOption).replace(
  /_C1锁HP\r?\n_L 0x6071D46C 0x0000270F\r?\n_L 0x00010001 0x00000798/,
  '_C1 锁HP9999_与高HP二选一\r\n_L 0x6071D46C 0x0000270F\r\n_L 0x00020001 0x00000798'
);
assert.match(candidate, /_C1 锁HP9999_与高HP二选一\r\n_L 0x6071D46C 0x0000270F\r\n_L 0x00020001/);
await fs.writeFile(path.join(root, 'UCAS40234.repaired.ini'), candidate);
await fs.writeFile(path.join(root, 'UCAS40234.before-attack-repair.ini'), original, { flag: 'wx' }).catch(error => {
  if (error.code !== 'EEXIST') throw error;
});

// Interpret the simple pointer writes with the semantics in PPSSPP v1.19.3.
// Check every target and verify no byte outside the intended six int32 fields changes.
const before = await fs.readFile(path.join(root, 'stage-RAM.dump'));
const memory = Buffer.from(before);
const ramBase = 0x08800000;
const actor = memory.readUInt32LE(0x08f1d46c - ramBase);
const changed = new Set();
for (const offset of attackOffsets) {
  const destination = actor + offset - ramBase;
  memory.writeUInt32LE(3100, destination);
  assert.equal(memory.readUInt32LE(destination), 3100);
  for (let byte = destination; byte < destination + 4; byte++) changed.add(byte);
}
for (let i = 0; i < before.length; i++) {
  if (!changed.has(i)) assert.equal(memory[i], before[i], `Unexpected change at ${hex(ramBase + i)}`);
}
assert.equal(memory.readUInt32LE(actor + 0x798 - ramBase), 9999, 'HP must stay unchanged');
assert.equal(memory.readUInt16LE(actor + 0x7a4 - ramBase), 999, 'SP must stay unchanged');
assert.equal(memory.readUInt32LE(0x089e64b0 - ramBase), before.readUInt32LE(0x089e64b0 - ramBase));
const report = {
  environment: 'PPSSPP v1.19.3 / UCAS40234 1.00',
  enabledAttackMultiplier: 32,
  percentBonus: 3100,
  targetOffsets: attackOffsets.map(hex),
  currentTargets: attackOffsets.map(offset => hex(actor + offset)),
  offlineSnapshotWriteCheck: 'passed',
  unrelatedBytesUnchanged: true,
  originalFileUnchanged: original.equals(await fs.readFile(source)),
};
await fs.writeFile(path.join(root, 'attack-repair-validation.json'), JSON.stringify(report, null, 2));

// Only the existing isolated PPSSPP copy receives the candidate for runtime verification.
const testCheats = path.join(root, 'PPSSPP-1.19.3/memstick/PSP/Cheats/UCAS40234.ini');
await fs.writeFile(testCheats, candidate);
const cfgPath = path.join(root, 'PPSSPP-1.19.3/memstick/PSP/SYSTEM/ppsspp.ini');
let cfg = await fs.readFile(cfgPath, 'utf8');
cfg = cfg.replace(/^EnableCheats\s*=.*$/m, 'EnableCheats = True')
  .replace(/^RemoteDebuggerOnStartup\s*=.*$/m, 'RemoteDebuggerOnStartup = True')
  .replace(/^RemoteISOPort\s*=.*$/m, 'RemoteISOPort = 26183')
  .replace(/^PauseOnLostFocus\s*=.*$/m, 'PauseOnLostFocus = False');
await fs.writeFile(cfgPath, cfg);
console.log(JSON.stringify(report, null, 2));
