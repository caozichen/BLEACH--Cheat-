import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));
const ws = new WebSocket('ws://[::1]:26183/debugger');
const pending = new Map();
let seq = 0;
await new Promise((resolve, reject) => {
  const timeout = setTimeout(() => reject(new Error('Debugger connection timed out')), 10000);
  ws.addEventListener('open', () => { clearTimeout(timeout); resolve(); });
  ws.addEventListener('error', error => { clearTimeout(timeout); reject(error); });
});
ws.addEventListener('message', message => {
  const result = JSON.parse(message.data);
  if (pending.has(result.ticket)) {
    pending.get(result.ticket)(result);
    pending.delete(result.ticket);
  }
});
async function call(event, data = {}) {
  const ticket = String(++seq);
  return await new Promise((resolve, reject) => {
    const timer = setTimeout(() => { pending.delete(ticket); reject(new Error(`Timeout: ${event}`)); }, 10000);
    pending.set(ticket, result => { clearTimeout(timer); result.event === 'error' ? reject(new Error(JSON.stringify(result))) : resolve(result); });
    ws.send(JSON.stringify({ event, ticket, ...data }));
  });
}
try {
  const result = { version: await call('version'), game: await call('game.status') };
  const ptr = await call('memory.read_u32', { address: 0x08f1d46c });
  result.playerPointer = ptr.value;
  if (ptr.value) {
    const block = await call('memory.read', { address: ptr.value + 0x918, size: 24 });
    const bytes = Buffer.from(block.base64, 'base64');
    result.attackBonuses = Array.from({length:6}, (_, i) => bytes.readInt32LE(i * 4));
    result.hp = (await call('memory.read_u32', { address: ptr.value + 0x798 })).value;
    result.maxHp = (await call('memory.read_u32', { address: ptr.value + 0x8e8 })).value;
    result.sp = (await call('memory.read_u16', { address: ptr.value + 0x7a4 })).value;
  }
  await fs.writeFile(path.join(root, 'attack-runtime-validation.json'), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 2));
} finally {
  ws.close();
}
