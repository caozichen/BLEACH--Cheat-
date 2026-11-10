import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const ATTACK_OFFSETS = [0x918, 0x91c, 0x920, 0x924, 0x928, 0x92c];
export const MULTIPLIERS = [32, 16, 64, 1];
const hex = n => `0x${n.toString(16).padStart(8, '0').toUpperCase()}`;
const writePointer = (offset, value) => `_L 0x6071D46C ${hex(value)}\r\n_L 0x00020001 ${hex(offset)}\r\n`;

export function buildCheats(original, { multiplier = 32, hp = 9999, defense = false } = {}) {
  if (!MULTIPLIERS.includes(multiplier)) throw new Error('攻击倍率必须为 1、16、32 或 64。');
  if (![9999, 99999].includes(hp)) throw new Error('HP 必须为 9999 或 99999。');
  if (!/^_S UCAS-40234\r?$/m.test(original)) throw new Error('输入不是 UCAS40234 金手指。');
  const blocks = original.split(/(?=^_C[0-9])/m);
  const attack = blocks.findIndex(block => block.includes('0x60000FF8 0x0000FFFF'));
  if (attack < 0 || !blocks[attack].includes('0x00020006 0x000003B4')) {
    throw new Error('未找到待修复的原攻击段；请使用 materials/UCAS40234.original.ini。');
  }
  blocks[attack] = MULTIPLIERS.map(m =>
    `_C${m === multiplier ? 1 : 0} 攻击倍率${m}倍_同类仅开一项\r\n` +
    ATTACK_OFFSETS.map(offset => writePointer(offset, (m - 1) * 100)).join('') + '\r\n'
  ).join('');
  const hpOption = `_C${hp === 99999 ? 1 : 0} 锁HP99999_与原锁HP二选一\r\n` +
    writePointer(0x798, 99999) + writePointer(0x8e8, 99999);
  const defenseOption = `_C${defense ? 1 : 0} 防御力9999_降低普通物理伤害\r\n` + writePointer(0x8f4, 9999);
  let output = blocks.join('') + '\r\n' + hpOption + '\r\n' + defenseOption;
  const oldHp = /_C1锁HP\r?\n_L 0x6071D46C 0x0000270F\r?\n_L 0x00010001 0x00000798/;
  if (!oldHp.test(output)) throw new Error('未找到预期的原锁 HP 段，已停止生成。');
  output = output.replace(oldHp,
    `_C${hp === 9999 ? 1 : 0} 锁HP9999_与高HP二选一\r\n_L 0x6071D46C 0x0000270F\r\n_L 0x00020001 0x00000798`);
  return output;
}

async function main() {
  const options = { multiplier: 32, hp: 9999, defense: false };
  let source = path.join(ROOT, 'materials/UCAS40234.original.ini');
  let destination = path.join(ROOT, 'cheats/UCAS40234.ini');
  const args = process.argv.slice(2);
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--help') {
      console.log('node scripts/build-cheats.mjs [--multiplier 1|16|32|64] [--hp 9999|99999] [--defense] [--source FILE] [--output FILE]');
      return;
    }
    if (arg === '--defense') options.defense = true;
    else if (['--source', '--output', '--multiplier', '--hp'].includes(arg)) {
      const value = args[++i];
      if (!value) throw new Error(`${arg} 缺少参数。`);
      if (arg === '--source') source = path.resolve(value);
      else if (arg === '--output') destination = path.resolve(value);
      else options[arg.slice(2)] = Number(value);
    } else throw new Error(`未知参数：${arg}`);
  }
  if (path.resolve(source) === path.resolve(destination)) throw new Error('输入与输出必须是不同文件。');
  const output = buildCheats(await fs.readFile(source, 'utf8'), options);
  await fs.mkdir(path.dirname(destination), { recursive: true });
  await fs.writeFile(destination, output, 'utf8');
  console.log(JSON.stringify({ output: destination, ...options, game: 'UCAS40234 / 1.00',
    note: '仅生成文件；没有安装到模拟器，也没有启动游戏。' }, null, 2));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(error => { console.error(error.message); process.exitCode = 1; });
}
