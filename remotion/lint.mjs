// node lint.mjs props.json out.json [mỗi_giây=0.5]
// Dựng thử ảnh nhỏ mỗi 0.5 giây với máy đo bố cục (src/probe.tsx), gom kết quả thành out.json:
// {"fps", "duration", "frames": [{"t", "texts", "issues"}]}. Không xuất video, chỉ để soát lỗi trình bày.
import {bundle} from '@remotion/bundler';
import {renderFrames, selectComposition} from '@remotion/renderer';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const [, , propsPath, outPath, stepArg] = process.argv;
const inputProps = {...JSON.parse(fs.readFileSync(propsPath, 'utf8')), lint: true};
delete inputProps.audio;   // không cần tiếng khi đo
const id = inputProps.comp || (inputProps.height > inputProps.width ? 'InsightShort' : 'Insight');
const browserExecutable = process.env.CHROME_PATH || (fs.existsSync('/usr/bin/google-chrome') ? '/usr/bin/google-chrome' : null);
const chromiumOptions = {gl: 'angle', enableMultiProcessOnLinux: true};

const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts'), publicDir: path.resolve('public')});
const composition = await selectComposition({serveUrl, id, inputProps, browserExecutable, chromiumOptions});
const step = Math.max(1, Math.round(Number(stepArg || 0.5) * composition.fps));
const frames = new Map();
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'lint-'));
await renderFrames({
  composition, serveUrl, inputProps, browserExecutable, chromiumOptions, outputDir: dir, imageFormat: 'jpeg', jpegQuality: 40,
  scale: 0.25, everyNthFrame: step, concurrency: Number(process.env.CONCURRENCY || 0) || null, timeoutInMilliseconds: 60000,
  onStart: () => {}, onFrameUpdate: () => {},
  onBrowserLog: (log) => {
    const i = log.text.indexOf('LAYOUT_JSON ');
    if (i < 0) return;
    try {
      const d = JSON.parse(log.text.slice(i + 12));
      frames.set(d.f, {t: +(d.f / composition.fps).toFixed(2), texts: d.texts || [], issues: d.issues || [], error: d.error});
    } catch {}
  },
});
fs.rmSync(dir, {recursive: true, force: true});
const out = {fps: composition.fps, duration: composition.durationInFrames / composition.fps,
  frames: [...frames.values()].sort((a, b) => a.t - b.t)};
fs.writeFileSync(outPath, JSON.stringify(out));
console.log(`lint ${out.frames.length} khung, ${out.frames.reduce((n, x) => n + x.issues.length, 0)} lỗi`);
