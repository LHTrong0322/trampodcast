import React, {useEffect, useState} from 'react';
import {
  AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig,
  continueRender, delayRender, Easing,
} from 'remotion';

export const C = {
  bg: '#07060f',
  ink: '#F6F3FF',
  muted: '#A9A3C7',
  violet: '#7B5CFF',
  cyan: '#22D3EE',
  pink: '#FF4FD8',
  gold: '#FFC83D',
  green: '#2EE59D',
  red: '#FF5470',
};
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

// ---------- animated background ----------
export const Backdrop: React.FC<{accent?: string; img?: string; dim?: number}> = ({accent = C.violet, img, dim = 0.78}) => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const t = f / 30;
  const g1x = 30 + 12 * Math.sin(t * 0.21);
  const g1y = 25 + 10 * Math.cos(t * 0.17);
  const g2x = 75 + 10 * Math.cos(t * 0.13);
  const g2y = 80 + 8 * Math.sin(t * 0.19);
  return (
    <AbsoluteFill style={{background: C.bg, overflow: 'hidden'}}>
      {img ? (
        <Img src={staticFile(img)} style={{position: 'absolute', inset: -40, width: width + 80, height: height + 80,
          objectFit: 'cover', filter: 'blur(26px) saturate(1.2)', opacity: 1 - dim,
          transform: `scale(${1.05 + 0.03 * Math.sin(t * 0.2)})`}} />
      ) : null}
      <AbsoluteFill style={{
        background: `radial-gradient(circle at ${g1x}% ${g1y}%, ${accent}55 0%, transparent 42%),
                     radial-gradient(circle at ${g2x}% ${g2y}%, ${C.cyan}33 0%, transparent 40%),
                     radial-gradient(circle at 50% 120%, ${C.pink}22 0%, transparent 50%)`,
      }} />
      {/* perspective grid floor */}
      <AbsoluteFill style={{perspective: 900, overflow: 'hidden'}}>
        <div style={{
          position: 'absolute', left: '-50%', width: '200%', height: '70%', bottom: '-28%',
          transform: 'rotateX(72deg)', transformOrigin: 'center top',
          backgroundImage: `linear-gradient(${accent}40 2px, transparent 2px), linear-gradient(90deg, ${accent}40 2px, transparent 2px)`,
          backgroundSize: '90px 90px', backgroundPosition: `0 ${(f * 1.6) % 90}px`,
          maskImage: 'linear-gradient(to bottom, transparent, black 30%, black 60%, transparent)',
          opacity: 0.55,
        }} />
      </AbsoluteFill>
      <Particles />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.65) 100%)'}} />
    </AbsoluteFill>
  );
};

const P_SEEDS = Array.from({length: 38}, (_, i) => {
  const r = (n: number) => {
    const x = Math.sin(i * 999 + n * 77) * 10000;
    return x - Math.floor(x);
  };
  return {x: r(1), y: r(2), s: 2 + r(3) * 4, v: 0.15 + r(4) * 0.5, o: 0.2 + r(5) * 0.5};
});
const Particles: React.FC = () => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  return (
    <AbsoluteFill>
      {P_SEEDS.map((p, i) => {
        const y = ((p.y * height - f * p.v * 2) % height + height) % height;
        return <div key={i} style={{position: 'absolute', left: p.x * width, top: y, width: p.s, height: p.s,
          borderRadius: 99, background: i % 3 ? C.cyan : C.violet, opacity: p.o * (0.6 + 0.4 * Math.sin(f / 20 + i)),
          boxShadow: `0 0 ${p.s * 4}px ${i % 3 ? C.cyan : C.violet}`}} />;
      })}
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
        opacity: enter, boxShadow: `0 40px 120px rgba(0,0,0,0.6), 0 0 0 2px ${C.violet}99, 0 0 60px ${C.violet}55`}}>
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
  return (
    <div style={{display: 'flex', flexWrap: 'wrap', columnGap: size * 0.26, rowGap: size * (lineHeight - 1),
      maxWidth, fontFamily: FONT, fontWeight: weight, fontSize: size, lineHeight, color}}>
      {words.map((w, i) => {
        const s = spring({frame: f - delay - i * stagger, fps, config: {damping: 15, mass: 0.7}});
        const hl = highlight.some((h) => w.toLowerCase().includes(h.toLowerCase()));
        return (
          <span key={i} style={{display: 'inline-block', overflow: 'hidden', paddingBottom: size * 0.08}}>
            <span style={{display: 'inline-block', transform: `translateY(${(1 - s) * 110}%) rotate(${(1 - s) * 6}deg)`,
              opacity: s, color: hl ? C.gold : color, textShadow: hl ? `0 0 30px ${C.gold}88` : '0 4px 24px rgba(0,0,0,0.5)'}}>{w}</span>
          </span>
        );
      })}
    </div>
  );
};

// ---------- count-up stat ----------
export const CountUp: React.FC<{value: string; delay?: number; size: number; color?: string}> = ({value, delay = 0, size, color = C.gold}) => {
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
    textShadow: `0 0 40px ${color}99, 0 6px 30px rgba(0,0,0,0.6)`, letterSpacing: -2}}>{shown}</div>;
};

// ---------- TikTok-style captions ----------
export const Captions: React.FC<{words: Word[]; bottom: number; size: number; maxWidth: number; perChunk?: number}> = ({
  words, bottom, size, maxWidth, perChunk = 7,
}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  if (!words.length) return null;
  // chunk by count + punctuation
  const chunks: Word[][] = [];
  let cur: Word[] = [];
  words.forEach((w, i) => {
    cur.push(w);
    const end = /[.!?…,:;]$/.test(w.t);
    const gap = i + 1 < words.length && words[i + 1].s - w.e > 0.25;
    if (cur.length >= perChunk || (end && cur.length >= 3) || gap) {
      chunks.push(cur);
      cur = [];
    }
  });
  if (cur.length) chunks.push(cur);
  const ci = chunks.findIndex((c, i) => t < (chunks[i + 1]?.[0].s ?? Infinity));
  const chunk = chunks[Math.max(0, ci)];
  if (!chunk || t < chunk[0].s - 0.1 || t > chunk[chunk.length - 1].e + 0.6) return null;
  const pop = spring({frame: f - Math.round(chunk[0].s * fps), fps, config: {damping: 13, mass: 0.5}});
  return (
    <div style={{position: 'absolute', left: 0, right: 0, bottom, display: 'flex', justifyContent: 'center'}}>
      <div style={{maxWidth, display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: `${size * 0.12}px ${size * 0.24}px`,
        fontFamily: FONT, fontWeight: 800, fontSize: size, lineHeight: 1.15, transform: `scale(${interpolate(pop, [0, 1], [0.9, 1])})`,
        opacity: pop, padding: '14px 28px', borderRadius: 22, background: 'rgba(7,6,15,0.55)', backdropFilter: 'blur(8px)'}}>
        {chunk.map((w, i) => {
          const active = t >= w.s && t < w.e + 0.05;
          const done = t >= w.e;
          return <span key={i} style={{color: active ? '#0b0a14' : done ? C.ink : 'rgba(246,243,255,0.55)',
            background: active ? C.gold : 'transparent', borderRadius: 10, padding: '0 8px',
            transform: `scale(${active ? 1.08 : 1})`, display: 'inline-block',
            textShadow: active ? 'none' : '0 3px 12px rgba(0,0,0,0.8)'}}>{w.t}</span>;
        })}
      </div>
    </div>
  );
};

// ---------- glitch flash at scene start ----------
export const Glitch: React.FC<{frames?: number}> = ({frames = 10}) => {
  const f = useCurrentFrame();
  if (f > frames) return null;
  const k = 1 - f / frames;
  const bars = Array.from({length: 7}, (_, i) => {
    const x = Math.sin((f + 1) * (i + 3) * 12.9898) * 43758.5453;
    return x - Math.floor(x);
  });
  return (
    <AbsoluteFill style={{pointerEvents: 'none', mixBlendMode: 'screen'}}>
      <AbsoluteFill style={{background: `linear-gradient(90deg, ${C.cyan}${Math.round(k * 80).toString(16).padStart(2, '0')}, transparent, ${C.pink}${Math.round(k * 80).toString(16).padStart(2, '0')})`}} />
      {bars.map((b, i) => <div key={i} style={{position: 'absolute', left: 0, right: 0, top: `${b * 100}%`, height: 6 + b * 40,
        background: i % 2 ? C.cyan : C.pink, opacity: k * 0.6, transform: `translateX(${(b - 0.5) * 200 * k}px)`}} />)}
      <AbsoluteFill style={{background: '#fff', opacity: f < 2 ? 0.35 : 0}} />
    </AbsoluteFill>
  );
};

export const Chip: React.FC<{text: string; color?: string; size?: number}> = ({text, color = C.violet, size = 26}) => (
  <div style={{display: 'inline-flex', alignItems: 'center', gap: 10, padding: `${size * 0.35}px ${size * 0.8}px`, borderRadius: 99,
    background: `${color}26`, border: `2px solid ${color}AA`, color: C.ink, fontFamily: FONT, fontWeight: 700, fontSize: size,
    boxShadow: `0 0 24px ${color}44`}}>{text}</div>
);
