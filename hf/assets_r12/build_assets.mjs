import sharp from 'sharp';
import fs from 'fs';
const S = 3;
const R = { x: 28, y: 446, w: 374, h: 204 };      // css px region where typing / focus / press differ (identical geometry for every state)
const HL = { x: 36, y: 624, w: 358, h: 30 };      // "Za darmo" highlight band region
const crop = (src, dst, r) => sharp(src).extract({ left: r.x * S, top: r.y * S, width: r.w * S, height: r.h * S }).png({ compressionLevel: 9 }).toFile(dst);
fs.copyFileSync('full/base.png', 'page_base.png');
const names = ['t0', 't1', 't2', 't3', 't4', 't5', 't6', 't7', 't8', 't9', 'press', 'idle'];
for (const n of names) await crop(`full/${n}.png`, `s_${n}.png`, R);
await crop('full/highlight.png', 's_hl.png', HL);
console.log('ok');
