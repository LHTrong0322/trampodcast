import React, {useEffect, useState} from 'react';
import {
  AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig,
  continueRender, delayRender, Easing,
} from 'remotion';

// Bảng màu "sạch": nền xanh đen trung tính, 1 màu nhấn (đổi theo màu brand dự án), ít phát sáng
export const C = {
  bg: '#0A0C12',
  panel: '#121621',
  line: 'rgba(255,255,255,0.08)',
  ink: '#F4F6FA',
  muted: '#8B94A7',
  violet: '#7C6CFF',
  cyan: '#4CC9F0',
  pink: '#F472B6',
  gold: '#FFC94D',
  green: '#22C55E',
  red: '#F43F5E',
};
export const AccentCtx = React.createContext<string>('#7C6CFF');
export const useAccent = () => React.useContext(AccentCtx);
export const FONT = "'BVP', system-ui, sans-serif";

export type Word = {t: string; s: number; e: number};

// ---------- fonts ----------
const FONTS: [string, string][] = [
  ['400', 'fonts/BeVietnamPro-Regular.ttf'],
  ['600', 'fonts/BeVietnamPro-SemiBold.ttf'],
  ['700', 'fonts/BeVietnamPro-Bold.ttf'],
  ['800', 'fonts/BeVietnamPro-ExtraBold.ttf'],
];
let fontsLoaded: Promise<unknown> | null = null;
export const useFonts = () => {
  const [handle] = useState(() => delayRender('fonts'));
  useEffect(() => {
    if (!fontsLoaded) {
      fontsLoaded = Promise.all(
        FONTS.map(([w, f]) => new FontFace('BVP', `url(${staticFile(f)})`, {weight: w}).load().then((ff) => {
          (document.fonts as any).add(ff);
        })),
      );
    }
    fontsLoaded.then(() => continueRender(handle)).catch(() => continueRender(handle));
  }, [handle]);
};

export const ease = Easing.bezier(0.16, 1, 0.3, 1);
export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const useSpring = (delay = 0, damping = 14, mass = 0.8) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: f - delay, fps, config: {damping, mass}});
};

// ---------- nền: gradient nhẹ chuyển động chậm + ảnh mờ (nếu có), không lưới/hạt ----------
export const Backdrop: React.FC<{accent?: string; img?: string; dim?: number}> = ({accent, img, dim = 0.8}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const ctx = useAccent();
  const ac = accent || ctx;
  const t = f / 30;
  const x = 22 + 6 * Math.sin(t * 0.12);
  const y = 18 + 5 * Math.cos(t * 0.1);
  return (
    <AbsoluteFill style={{background: C.bg, overflow: 'hidden'}}>
      {img ? (
        <Img src={staticFile(img)} style={{position: 'absolute', inset: -40, width: width + 80, height: height + 80,
          objectFit: 'cover', filter: 'blur(30px) saturate(0.9)', opacity: 1 - dim,
          transform: `scale(${1.05 + 0.02 * Math.sin(t * 0.15)})`}} />
      ) : null}
      <AbsoluteFill style={{background: `radial-gradient(1100px 700px at ${x}% ${y}%, ${ac}26, transparent 70%),
        radial-gradient(900px 600px at 88% 92%, ${ac}14, transparent 70%)`}} />
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(10,12,18,0) 60%, rgba(10,12,18,0.85) 100%)'}} />
    </AbsoluteFill>
  );
};

// ---------- image card with ken burns + crossfade ----------
export const ImageDeck: React.FC<{images: string[]; dur: number; w: number; h: number; every?: number; tilt?: number; radius?: number}> = ({
  images, dur, w, h, every = 4, tilt = -8, radius = 34,
}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  const n = Math.max(1, images.length);
  const per = Math.max(every, dur / n);
  const idx = Math.min(n - 1, Math.floor(t / per));
  const local = t - idx * per;
  const enter = useSpring(4, 16);
  const ry = interpolate(enter, [0, 1], [tilt * 3, tilt]) + 2 * Math.sin(t * 0.5);
  return (
    <div style={{width: w, height: h, perspective: 1600}}>
      <div style={{width: w, height: h, borderRadius: radius, overflow: 'hidden', position: 'relative',
        transform: `rotateY(${ry}deg) rotateX(${3 * Math.sin(t * 0.4)}deg) scale(${interpolate(enter, [0, 1], [0.85, 1])})`,
        opacity: enter, boxShadow: `0 30px 80px rgba(0,0,0,0.5), 0 0 0 1px ${C.line}`}}>
        {images.length === 0 ? <div style={{width: '100%', height: '100%', background: '#15122a'}} /> : null}
        {images.map((src, i) => {
          if (Math.abs(i - idx) > 1) return null;
          const lt = t - i * per;
          const op = i === idx ? interpolate(lt, [0, 0.6], [i === 0 ? 1 : 0, 1], clamp) : i === idx - 1 ? interpolate(local, [0, 0.6], [1, 0], clamp) : 0;
          const z = 1.06 + 0.1 * (lt / per);
          const dx = (i % 2 ? -1 : 1) * 30 * (lt / per);
          return <Img key={i} src={staticFile(src)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%',
            objectFit: 'cover', opacity: op, transform: `scale(${z}) translateX(${dx}px)`,
            filter: `blur(${i === idx ? interpolate(lt, [0, 0.5], [12, 0], clamp) : 0}px)`}} />;
        })}
        <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(180deg, transparent 55%, rgba(7,6,15,0.85))'}} />
        {/* sheen */}
        <div style={{position: 'absolute', top: 0, bottom: 0, width: '40%', left: `${interpolate((t % 6) / 6, [0, 1], [-60, 160])}%`,
          background: 'linear-gradient(100deg, transparent, rgba(255,255,255,0.10), transparent)', transform: 'skewX(-12deg)'}} />
      </div>
    </div>
  );
};

// ---------- text reveal ----------
export const RevealWords: React.FC<{text: string; size: number; weight?: number; color?: string; delay?: number;
  stagger?: number; lineHeight?: number; maxWidth?: number; highlight?: string[]}> = ({
  text, size, weight = 800, color = C.ink, delay = 0, stagger = 3, lineHeight = 1.12, maxWidth, highlight = [],
}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = text.split(/\s+/).filter(Boolean);
  const accentColor = useAccent();
  return (
    <div style={{display: 'flex', flexWrap: 'wrap', columnGap: size * 0.26, rowGap: size * (lineHeight - 1),
      maxWidth, fontFamily: FONT, fontWeight: weight, fontSize: size, lineHeight, color}}>
      {words.map((w, i) => {
        const s = spring({frame: f - delay - i * stagger, fps, config: {damping: 15, mass: 0.7}});
        const hl = highlight.some((h) => h && w.toLowerCase().includes(h.toLowerCase()));
        return (
          <span key={i} style={{display: 'inline-block', overflow: 'hidden', paddingBottom: size * 0.08}}>
            <span style={{display: 'inline-block', transform: `translateY(${(1 - s) * 110}%) rotate(${(1 - s) * 6}deg)`,
              opacity: s, color: hl ? accentColor : color, textShadow: '0 2px 12px rgba(0,0,0,0.35)'}}>{w}</span>
          </span>
        );
      })}
    </div>
  );
};

// ---------- count-up stat ----------
export const CountUp: React.FC<{value: string; delay?: number; size: number; color?: string}> = ({value, delay = 0, size, color: col}) => {
  const ac = useAccent();
  const color = col || ac;
  const f = useCurrentFrame();
  const m = value.match(/^([^\d]*)(\d+(?:[.,]\d+)?)(.*)$/);
  let shown = value;
  if (m) {
    const target = parseFloat(m[2].replace(/,/g, ''));
    const dec = (m[2].split(/[.]/)[1] || '').length;
    const p = interpolate(f - delay, [0, 28], [0, 1], {...clamp, easing: ease});
    const v = target * p;
    const num = dec ? v.toFixed(dec) : m[2].includes(',') ? Math.round(v).toLocaleString('en-US') : String(Math.round(v));
    shown = m[1] + num + m[3];
  }
  const s = useSpring(delay, 10, 0.6);
  return <div style={{fontFamily: FONT, fontWeight: 800, fontSize: size, color, lineHeight: 1,
    transform: `scale(${interpolate(s, [0, 1], [0.6, 1])})`, opacity: s,
    textShadow: '0 4px 20px rgba(0,0,0,0.4)', letterSpacing: -1}}>{shown}</div>;
};

// ---------- phụ đề: hiện cả cụm câu (không chạy từng chữ), gọn & dễ đọc ----------
export const Captions: React.FC<{words: Word[]; bottom: number; size: number; maxWidth: number; perChunk?: number}> = ({
  words, bottom, size, maxWidth, perChunk = 12,
}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  if (!words.length) return null;
  const chunks: Word[][] = [];
  let cur: Word[] = [];
  words.forEach((w, i) => {
    cur.push(w);
    const stop = /[.!?…]$/.test(w.t);
    const comma = /[,;:]$/.test(w.t);
    const gap = i + 1 < words.length && words[i + 1].s - w.e > 0.3;
    if (cur.length >= perChunk || stop || (comma && cur.length >= 5) || gap) {
      chunks.push(cur);
      cur = [];
    }
  });
  if (cur.length) chunks.push(cur);
  const idx = chunks.findIndex((c, i) => t >= c[0].s - 0.05 && t < (chunks[i + 1]?.[0].s ?? c[c.length - 1].e + 0.4) - 0.05);
  if (idx < 0) return null;
  const c = chunks[idx];
  const op = interpolate(t - c[0].s, [-0.05, 0.12], [0, 1], clamp);
  return (
    <div style={{position: 'absolute', left: 0, right: 0, bottom, display: 'flex', justifyContent: 'center'}}>
      <div style={{maxWidth, textAlign: 'center', fontFamily: FONT, fontWeight: 600, fontSize: size, lineHeight: 1.3,
        color: C.ink, opacity: op, padding: '10px 26px', borderRadius: 14, background: 'rgba(10,12,18,0.72)',
        textShadow: '0 2px 8px rgba(0,0,0,0.6)'}}>
        {c.map((w) => w.t).join(' ')}
      </div>
    </div>
  );
};

// ---------- chuyển cảnh: mờ dần nhẹ (sạch hơn glitch) ----------
export const Glitch: React.FC<{frames?: number}> = ({frames = 9}) => {
  const f = useCurrentFrame();
  if (f > frames) return null;
  return <AbsoluteFill style={{background: C.bg, opacity: interpolate(f, [0, frames], [1, 0], clamp), pointerEvents: 'none'}} />;
};

export const Chip: React.FC<{text: string; color?: string; size?: number}> = ({text, color: col, size = 26}) => {
  const ac = useAccent();
  const color = col || ac;
  return <div style={{display: 'inline-flex', alignItems: 'center', gap: 10, padding: `${size * 0.32}px ${size * 0.75}px`, borderRadius: 99,
    background: `${color}1F`, border: `1.5px solid ${color}88`, color: C.ink, fontFamily: FONT, fontWeight: 700, fontSize: size,
    letterSpacing: 1}}>{text}</div>;
};
