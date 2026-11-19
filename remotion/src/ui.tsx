import React, {useEffect, useState} from 'react';
import {
  AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig,
  continueRender, delayRender, Easing,
} from 'remotion';

// Bảng màu "crypto cao cấp & sạch": nền tối xanh-tím sâu (không đen trơn), 1 quầng màu nhấn tím→xanh rất nhẹ,
// thẻ kính mờ tinh tế, chữ trắng; màu nổi chỉ dùng cho số liệu. (blue = màu nhấn chính, sky = cyan, orange = màu số)
export const BRAND = {blue: '#8E9BFF', sky: '#A9B8FF', orange: '#FFFFFF', navy: '#0C0E24', pink: '#B9A8FF'};
export const C = {
  bg: '#0C0E24',
  panel: 'rgba(255,255,255,0.05)',
  line: 'rgba(255,255,255,0.10)',
  ink: '#F7F8FC',
  muted: '#A9AECB',
  violet: '#8E9BFF',
  cyan: '#A9B8FF',
  pink: '#B9A8FF',
  gold: '#E8EAF6',
  green: '#3CC48D',
  red: '#E5677D',
};
export const glass: React.CSSProperties = {background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.10)',
  backdropFilter: 'blur(14px)', boxShadow: '0 20px 60px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.06)'};
export const AccentCtx = React.createContext<string>(BRAND.blue);
export const useAccent = () => React.useContext(AccentCtx);
export const FONT = "'BODY', system-ui, sans-serif";      // chữ thường, phụ đề: Lexend (dễ đọc)
export const HEAD = "'HEAD', 'BODY', sans-serif";         // tiêu đề: Space Grotesk (hiện đại, tech)
export const DISPLAY = "'DISPLAY', 'HEAD', sans-serif";   // số lớn, ảnh bìa: Unbounded (chất crypto)

export type Word = {t: string; s: number; e: number};

// ---------- fonts (Lexend + Space Grotesk + Unbounded, có tiếng Việt) ----------
import FONT_LIST from './fonts.json';
let fontsLoaded: Promise<unknown> | null = null;
export const useFonts = () => {
  const [handle] = useState(() => delayRender('fonts'));
  useEffect(() => {
    if (!fontsLoaded) {
      fontsLoaded = Promise.all(
        (FONT_LIST as any[]).map((x) => new FontFace(x.family, `url(${staticFile(x.file)})`, {weight: x.weight, unicodeRange: x.range})
          .load().then((ff) => (document.fonts as any).add(ff)).catch(() => null)),
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

// ---------- nền: gradient tím điện → xanh dương + 3 mảng màu (tím/cyan/hồng) trôi chậm + lưới chấm ----------
export const Backdrop: React.FC<{accent?: string; img?: string; dim?: number}> = ({accent, img, dim = 0.8}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const ctx = useAccent();
  const ac = accent || ctx;
  const t = f / 30;
  const blob = (cx: number, cy: number, r: number, col: string, a: number, sp: number, ph: number) => (
    <div style={{position: 'absolute', left: `${cx + 7 * Math.sin(t * sp + ph)}%`, top: `${cy + 6 * Math.cos(t * sp * 0.8 + ph)}%`,
      width: r, height: r, marginLeft: -r / 2, marginTop: -r / 2, borderRadius: '50%', background: col, opacity: a, filter: 'blur(120px)'}} />
  );
  return (
    <AbsoluteFill style={{background: 'linear-gradient(150deg, #141436 0%, #0C0E24 50%, #0A1530 100%)', overflow: 'hidden'}}>
      {img ? (
        <Img src={staticFile(img)} style={{position: 'absolute', inset: -40, width: width + 80, height: height + 80,
          objectFit: 'cover', filter: 'blur(26px) saturate(1.2)', opacity: 1 - dim, mixBlendMode: 'screen',
          transform: `scale(${1.05 + 0.02 * Math.sin(t * 0.15)})`}} />
      ) : null}
      {blob(15, 18, 900, ac, 0.18, 0.1, 0)}
      {blob(88, 85, 800, BRAND.sky, 0.08, 0.08, 2)}
      <AbsoluteFill style={{backgroundImage: 'radial-gradient(rgba(255,255,255,0.07) 1.4px, transparent 1.4px)', backgroundSize: '36px 36px',
        backgroundPosition: `${(f * 0.25) % 36}px 0px`,
        maskImage: 'radial-gradient(ellipse 85% 75% at 65% 40%, black 15%, transparent 80%)'}} />
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(8,6,40,0) 65%, rgba(8,6,40,0.7) 100%)'}} />
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
      maxWidth, fontFamily: HEAD, fontWeight: weight >= 700 ? 700 : 500, fontSize: size, lineHeight, color, letterSpacing: -0.5}}>
      {words.map((w, i) => {
        const s = spring({frame: f - delay - i * stagger, fps, config: {damping: 15, mass: 0.7}});
        const hl = highlight.some((h) => h && w.toLowerCase().includes(h.toLowerCase()));
        return (
          <span key={i} style={{display: 'inline-block', overflow: 'hidden', paddingBottom: size * 0.08}}>
            <span style={{display: 'inline-block', transform: `translateY(${(1 - s) * 110}%) rotate(${(1 - s) * 6}deg)`,
              opacity: s, color: color, textShadow: hl ? 'none' : '0 2px 12px rgba(0,0,0,0.3)',
              ...(hl ? {color: accentColor} : {})}}>{w}</span>
          </span>
        );
      })}
    </div>
  );
};

// ---------- số đếm: chạy số ~1,5s, nảy nhẹ khi xong ----------
export const CountUp: React.FC<{value: string; delay?: number; size: number; color?: string; frames?: number}> = ({value, delay = 0, size, color: col, frames = 45}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = useAccent();
  const color = col || ac;
  const m = value.match(/^([^\d]*)(\d+(?:[.,]\d+)?)(.*)$/);
  let shown = value;
  if (m) {
    const target = parseFloat(m[2].replace(/,/g, ''));
    const dec = (m[2].split(/[.]/)[1] || '').length;
    const p = interpolate(f - delay, [0, frames], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
    const v = target * p;
    const num = dec ? v.toFixed(dec) : m[2].includes(',') ? Math.round(v).toLocaleString('en-US') : String(Math.round(v));
    shown = m[1] + num + m[3];
  }
  const s = spring({frame: f - delay, fps, config: {damping: 11, mass: 0.6}});
  const bump = spring({frame: f - delay - frames, fps, config: {damping: 8, mass: 0.4}});
  const sc = interpolate(s, [0, 1], [0.6, 1]) * (1 + 0.08 * Math.sin(Math.min(1, bump) * Math.PI));
  return <div style={{fontFamily: DISPLAY, fontWeight: 800, fontSize: size, color, lineHeight: 1, transform: `scale(${sc})`, opacity: s,
    textShadow: '0 6px 24px rgba(0,0,0,0.35)', letterSpacing: -2, fontVariantNumeric: 'tabular-nums'}}>{shown}</div>;
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
      <div style={{maxWidth, textAlign: 'center', fontFamily: FONT, fontWeight: 500, fontSize: size, lineHeight: 1.35,
        color: C.ink, opacity: op, padding: '10px 26px', borderRadius: 14, background: 'rgba(10,12,30,0.7)', backdropFilter: 'blur(8px)',
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
  return <AbsoluteFill style={{background: '#0C0E24', opacity: interpolate(f, [0, frames], [1, 0], clamp), pointerEvents: 'none'}} />;
};

export const Chip: React.FC<{text: string; color?: string; size?: number}> = ({text, color: col, size = 26}) => {
  const ac = useAccent();
  const color = col || ac;
  return <div style={{display: 'inline-flex', alignItems: 'center', gap: 10, padding: `${size * 0.32}px ${size * 0.75}px`, borderRadius: 99,
    background: `${color}24`, border: `1.5px solid ${color}99`, color: C.ink, fontFamily: HEAD, fontWeight: 700, fontSize: size,
    letterSpacing: 1}}>{text}</div>;
};

// logo X + @Trong0322 (watermark kênh)
export const XMark: React.FC<{size: number; color?: string}> = ({size, color = '#fff'}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={{display: 'inline-block', flexShrink: 0}}>
    <path fill={color} d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
  </svg>
);
export const Handle: React.FC<{size: number; color?: string; style?: React.CSSProperties}> = ({size, color = 'rgba(255,255,255,0.55)', style}) => (
  <div style={{display: 'flex', alignItems: 'center', gap: size * 0.35, fontFamily: HEAD, fontWeight: 700, fontSize: size, color, ...style}}>
    <XMark size={size * 0.9} color={color} />@Trong0322
  </div>
);
