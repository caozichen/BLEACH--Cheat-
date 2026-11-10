import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { buildCheats, ROOT } from '../scripts/build-cheats.mjs';

const original = await fs.readFile(`${ROOT}/materials/UCAS40234.original.ini`, 'utf8');
const shipped = await fs.readFile(`${ROOT}/cheats/UCAS40234.ini`, 'utf8');
const parseBlocks = text => text.split(/(?=^_C[01])/m).filter(t => /^_C[01]/.test(t));

test('default build reproduces the installed, runtime-verified INI byte for byte', () => {
  assert.equal(buildCheats(original), shipped);
});

test('every attack option is a complete set of six single-level 32-bit pointer writes', () => {
  const blocks = parseBlocks(shipped).filter(t => /^_C[01] 攻击倍率/.test(t));
  assert.equal(blocks.length, 4);
  for (const block of blocks) {
    const m = Number(block.match(/攻击倍率(\d+)倍/)[1]);
    const lines = [...block.matchAll(/^_L (0x[0-9A-F]+) (0x[0-9A-F]+)/gm)]
      .map(match => match.slice(1).map(Number));
    assert.equal(lines.length, 12);
    const actual = [];
    for (let i = 0; i < lines.length; i += 2) {
      // Decode the pointer command using the CWCheat command layout, independently
      // of the generator: 0x6 + pointer address; width=2 (word), count=1.
      assert.equal(lines[i][0] >>> 28, 6);
      assert.equal((lines[i][0] & 0x0fffffff) + 0x08800000, 0x08f1d46c);
      assert.equal((lines[i + 1][0] >>> 16) & 0xf, 2);
      assert.equal(lines[i + 1][0] & 0xffff, 1);
      actual.push([lines[i + 1][1], lines[i][1]]);
    }
    assert.deepEqual(actual, [0x918, 0x91c, 0x920, 0x924, 0x928, 0x92c].map(offset => [offset, (m - 1) * 100]));
  }
});

test('high HP selects one lock and updates current and maximum HP using 32-bit writes', () => {
  const output = buildCheats(original, { multiplier: 64, hp: 99999, defense: true });
  assert.match(output, /^_C0 锁HP9999_/m);
  assert.match(output, /^_C1 锁HP99999_/m);
  assert.match(output, /^_C1 防御力9999_/m);
  assert.equal((output.match(/^_C1 攻击倍率/gm) ?? []).length, 1);
  assert.match(output, /^_C1 攻击倍率64倍/m);
  const hp = parseBlocks(output).find(t => /^_C1 锁HP99999_/.test(t));
  assert.match(hp, /0x0001869F\r\n_L 0x00020001 0x00000798/);
  assert.match(hp, /0x0001869F\r\n_L 0x00020001 0x000008E8/);
});

test('unrelated original cheat blocks are preserved exactly', () => {
  const output = buildCheats(original);
  for (const block of parseBlocks(original)) {
    if (block.includes('0x60000FF8') || /^_C1锁HP/.test(block)) continue;
    assert.ok(output.includes(block), block.split('\n')[0]);
  }
});

test('wrong game, incompatible source, and unsupported values fail clearly', () => {
  assert.throws(() => buildCheats(original.replace('UCAS-40234', 'UCAS-00000')), /ID|UCAS40234/);
  assert.throws(() => buildCheats(shipped), /原攻击段/);
  assert.throws(() => buildCheats(original, { multiplier: 999999999 }), /攻击倍率/);
  assert.throws(() => buildCheats(original, { hp: 1 }), /HP/);
});
