// node render.mjs props.json out.mp4   (ONLY_FRAMES="3,40,90" → chỉ xuất ảnh khung hình để kiểm tra)
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';

const [, , propsPath, outPath] = process.argv;
const inputProps = JSON.parse(fs.readFileSync(propsPath, 'utf8'));
const id = inputProps.comp || (inputProps.height > inputProps.width ? 'InsightShort' : 'Insight');
const browserExecutable = process.env.CHROME_PATH || (fs.existsSync('/usr/bin/google-chrome') ? '/usr/bin/google-chrome' : null);
const chromiumOptions = {gl: 'angle', enableMultiProcessOnLinux: true};

const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts'), publicDir: path.resolve('public')});
const composition = await selectComposition({serveUrl, id, inputProps, browserExecutable, chromiumOptions});
const only = process.env.ONLY_FRAMES;
if (only) {
  for (const s of only.split(',').map(Number)) {
    const frame = Math.min(composition.durationInFrames - 1, Math.round(s * composition.fps));
    const out = outPath.endsWith('.png') ? outPath : outPath.replace(/\.mp4$/, '') + `-f${s}.png`;
    await renderStill({composition, serveUrl, output: out, frame, inputProps, browserExecutable, chromiumOptions});
    console.log('still', out);
  }
} else {
  let last = -1;
  await renderMedia({
    composition, serveUrl, codec: 'h264', outputLocation: outPath, inputProps, browserExecutable, chromiumOptions,
    // Thông số nguồn sạch cho bước hậu kỳ platform_export.py (nó mã hoá lại theo chuẩn YouTube/TikTok/Reels):
    // CRF 16 (ít mất chi tiết), màu BT.709, 4:2:0, âm thanh AAC 320k. LONG_RENDER_SCALE=1.3333 → dựng thẳng 1440p
    // cho video dài (chữ nét hơn nâng cấp bằng ffmpeg nhưng chậm hơn ~1,5-1,8 lần; mặc định 1 = 1080p rồi nâng 1440p).
    crf: 16, pixelFormat: 'yuv420p', colorSpace: 'bt709', audioCodec: 'aac', audioBitrate: '320k',
    scale: composition.width > composition.height ? Number(process.env.LONG_RENDER_SCALE || 1) : 1,
    concurrency: Number(process.env.CONCURRENCY || 0) || null, licenseKey: 'free-license',
    onProgress: ({progress}) => {
      const p = Math.floor(progress * 20);
      if (p !== last) { last = p; console.log(`render ${Math.round(progress * 100)}%`); }
    },
  });
  console.log('done', outPath);
}
