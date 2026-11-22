import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Backdrop, C, clamp, CountUp, ease, FONT, useFonts} from './ui';

// Màn hook kiểu "cú sốc": số lớn + đường giá đổ + từng thẻ tài sản bật theo lời đọc,
// rồi chuyển sang câu hỏi lớn với quả bóng nứt. Nền sạch (Trọng 22/11: không dùng nền màu tối).
export type HookImpactProps = {
  value: string;                 // vd "-$6T"
  label: string;                 // dòng dưới số, vd "bốc hơi trong 45 ngày"
  tag?: string;                  // nhãn dán, vd "45 NGÀY"
  chips: {text: string; s: number}[];   // thẻ tài sản, s = giây bật lên (theo lời đọc)
  question: string;              // vd "AI BUBBLE ĐÃ VỠ?"
  sub?: string;                  // vd "Hay cú rũ trước cơ hội lớn?"
  qAt: number;                   // giây chuyển sang câu hỏi
  subAt?: number;
  tone?: 'down' | 'up';
};

// đường giá trang trí: đổ dốc có nhịp hồi nhỏ, cố định (không phải dữ liệu thật, không có trục/số)
const PATH_PTS = [0.18, 0.16, 0.22, 0.2, 0.27, 0.25, 0.33, 0.38, 0.35, 0.44, 0.5, 0.47, 0.56, 0.62, 0.6, 0.7, 0.76, 0.73, 0.82, 0.9];

const Drop: React.FC<{p: number; col: string; w: number; h: number}> = ({p, col, w, h}) => {
  const pts = PATH_PTS.map((y, i) => [(i / (PATH_PTS.length - 1)) * w, 80 + y * (h - 160)]);
  const d = pts.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
  const len = w * 1.35;
  return (
    <svg width={w} height={h} style={{position: 'absolute', left: 0, top: 0}}>
      <defs>
        <linearGradient id="dropfill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={col} stopOpacity={0.16} />
          <stop offset="1" stopColor={col} stopOpacity={0} />
        </linearGradient>
        <clipPath id="dropclip"><rect x={0} y={0} width={w * p} height={h} /></clipPath>
      </defs>
      <path d={`${d} L${w},${h} L0,${h} Z`} fill="url(#dropfill)" clipPath="url(#dropclip)" />
      <path d={d} fill="none" stroke={col} strokeWidth={7} strokeLinejoin="round" strokeLinecap="round"
        strokeDasharray={len} strokeDashoffset={len * (1 - p)} opacity={0.55} />
    </svg>
  );
};

const Bubble: React.FC<{size: number; crack: number; pop: number; bob?: number}> = ({size, crack, pop, bob = 0}) => (
  <svg width={size} height={size} viewBox="0 0 200 200" style={{transform: `scale(${pop})`}}>
    <defs>
      <radialGradient id="bub" cx="35%" cy="30%" r="75%">
        <stop offset="0" stopColor="#FFFFFF" />
        <stop offset="0.55" stopColor="#E6E3FF" />
        <stop offset="1" stopColor="#B9B1FF" />
      </radialGradient>
    </defs>
    <circle cx="100" cy="100" r="88" fill="url(#bub)" stroke="#7C6CFF" strokeWidth="4" />
    {/* robot AI dễ thương (Trọng 23/11: dùng hình robot thay chữ AI), vẽ riêng bằng SVG */}
    <defs>
      <linearGradient id="rbWhite" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#FFFFFF" /><stop offset="1" stopColor="#D9DCE6" />
      </linearGradient>
      <linearGradient id="rbVisor" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#1E3550" /><stop offset="1" stopColor="#0B1626" />
      </linearGradient>
    </defs>
    <g transform={`translate(100 ${104 + bob}) scale(0.78)`}>
      <ellipse cx="0" cy="98" rx="34" ry="5" fill="#131836" opacity="0.12" />
      {/* tay */}
      <rect x="-64" y="20" width="20" height="50" rx="10" fill="url(#rbWhite)" transform="rotate(12 -54 20)" />
      <rect x="44" y="20" width="20" height="50" rx="10" fill="url(#rbWhite)" transform="rotate(-12 54 20)" />
      {/* thân */}
      <path d="M-42 22 Q-46 84 0 86 Q46 84 42 22 Q30 6 0 6 Q-30 6 -42 22 Z" fill="url(#rbWhite)" />
      <path d="M-40 50 L-12 50 L-8 56 L8 56 L12 50 L40 50" fill="none" stroke="#B8BDCC" strokeWidth="2" />
      <ellipse cx="-22" cy="30" rx="6" ry="12" fill="#FFFFFF" opacity="0.9" transform="rotate(25 -22 30)" />
      {/* cổ */}
      <rect x="-14" y="-6" width="28" height="16" rx="6" fill="#C9CDD9" />
      {/* tai */}
      <rect x="-66" y="-52" width="16" height="30" rx="7" fill="url(#rbWhite)" />
      <rect x="50" y="-52" width="16" height="30" rx="7" fill="url(#rbWhite)" />
      {/* đầu */}
      <rect x="-20" y="-88" width="40" height="12" rx="6" fill="url(#rbWhite)" />
      <rect x="-56" y="-80" width="112" height="76" rx="30" fill="url(#rbWhite)" />
      <rect x="-48" y="-72" width="96" height="58" rx="22" fill="url(#rbVisor)" />
      {/* mắt + miệng phát sáng */}
      <path d="M-30 -40 Q-21 -54 -12 -40 Z" fill="#4FE3F0" />
      <path d="M12 -40 Q21 -54 30 -40 Z" fill="#4FE3F0" />
      <path d="M-7 -30 Q0 -20 7 -30 Z" fill="#4FE3F0" />
      <ellipse cx="-34" cy="-66" rx="10" ry="4" fill="#FFFFFF" opacity="0.18" />
    </g>
    <path d="M58 46 Q60 58 72 60 Q60 62 58 74 Q56 62 44 60 Q56 58 58 46 Z" fill="#FFC83D" stroke="#131836" strokeWidth="2.5" />
    <path d="M154 134 Q155 141 162 142 Q155 143 154 150 Q153 143 146 142 Q153 141 154 134 Z" fill="#FFC83D" stroke="#131836" strokeWidth="2" />
    <path d="M150 28 L138 52 L158 66 L146 84" fill="none" stroke={C.red} strokeWidth="6" strokeLinecap="round" strokeLinejoin="round"
      strokeDasharray="90" strokeDashoffset={90 * (1 - crack)} />
    <path d="M158 66 L178 64" fill="none" stroke={C.red} strokeWidth="5" strokeLinecap="round" strokeDasharray="40" strokeDashoffset={40 * (1 - crack)} />
  </svg>
);

export const HookImpact: React.FC<HookImpactProps> = ({value, label, tag, chips, question, sub, qAt, subAt, tone = 'down'}) => {
  useFonts();
  const f = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const t = f / fps;
  const col = tone === 'down' ? C.red : C.green;
  const k = interpolate(t, [qAt - 0.15, qAt + 0.45], [0, 1], {...clamp, easing: ease});   // 0 = màn số, 1 = màn câu hỏi
  const draw = interpolate(t, [0.1, 1.8], [0, 1], {...clamp, easing: ease});
  const shake = t < 0.5 ? Math.sin(t * 90) * (0.5 - t) * 14 : 0;
  const numScale = interpolate(k, [0, 1], [1, 0.42]);
  const numX = interpolate(k, [0, 1], [150, 110]);
  const numY = interpolate(k, [0, 1], [330, 70]);
  const qWords = question.split(' ');
  const sAt = subAt ?? qAt + 1.2;
  return (
    <AbsoluteFill>
      <Backdrop />
      <div style={{position: 'absolute', inset: 0, opacity: interpolate(k, [0, 1], [1, 0.35])}}>
        <Drop p={draw} col={col} w={width} h={height} />
      </div>
      {/* số lớn */}
      <div style={{position: 'absolute', left: numX, top: numY, transformOrigin: 'left top', transform: `scale(${numScale}) translateX(${shake}px)`}}>
        <CountUp value={value} size={330} color={col} delay={2} />
        <div style={{fontFamily: FONT, fontWeight: 800, fontSize: 58, color: C.ink, marginTop: 18, opacity: interpolate(t, [0.5, 0.9], [0, 1], clamp) * (1 - k)}}>{label}</div>
      </div>
      {/* nhãn dán */}
      {tag ? <div style={{position: 'absolute', left: 160, top: 205, opacity: interpolate(t, [0.7, 1.0], [0, 1], clamp) * (1 - k),
        transform: `rotate(-8deg) scale(${interpolate(t, [0.7, 1.0], [1.6, 1], {...clamp, easing: ease})})`,
        padding: '14px 30px', borderRadius: 18, background: '#FFE14D', border: `4px solid ${C.ink}`, boxShadow: '6px 6px 0 rgba(19,24,54,0.9)',
        fontFamily: FONT, fontWeight: 900, fontSize: 46, color: C.ink, letterSpacing: 2}}>{tag}</div> : null}
      {/* thẻ tài sản */}
      <div style={{position: 'absolute', right: 120, top: 330, display: 'flex', flexDirection: 'column', gap: 30, opacity: 1 - k}}>
        {chips.map((c, i) => {
          const p = interpolate(t, [c.s - 0.05, c.s + 0.3], [0, 1], {...clamp, easing: ease});
          const hit = interpolate(t, [c.s + 0.25, c.s + 0.45], [1.08, 1], clamp);
          return <div key={i} style={{display: 'flex', alignItems: 'center', gap: 22, padding: '22px 34px 22px 26px', borderRadius: 26, background: '#FFFFFF',
            border: `1px solid ${C.line}`, boxShadow: '0 16px 40px rgba(40,50,110,0.12)', opacity: p,
            transform: `translateX(${(1 - p) * 160}px) scale(${p < 1 ? 1 : hit})`, minWidth: 560}}>
            <div style={{width: 66, height: 66, borderRadius: 18, background: `${col}18`, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
              <svg width="34" height="34" viewBox="0 0 24 24"><path d={tone === 'down' ? 'M4 7 L12 18 L20 7 Z' : 'M4 17 L12 6 L20 17 Z'} fill={col} /></svg>
            </div>
            <div style={{fontFamily: FONT, fontWeight: 800, fontSize: 52, color: C.ink, flex: 1}}>{c.text}</div>
            <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 40, color: col}}>{tone === 'down' ? 'ĐỎ' : 'XANH'}</div>
          </div>;
        })}
      </div>
      {/* màn câu hỏi */}
      {k > 0 ? <div style={{position: 'absolute', left: 0, right: 0, top: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 56, opacity: k}}>
        <Bubble size={300} bob={Math.sin(t * 3) * 3} crack={interpolate(t, [qAt + 0.5, qAt + 1.1], [0, 1], clamp)}
          pop={interpolate(t, [qAt, qAt + 0.5], [0.6, 1], {...clamp, easing: ease}) * (1 + 0.025 * Math.sin(t * 5))} />
        <div style={{display: 'flex', flexDirection: 'column', gap: 26, maxWidth: 1420}}>
          <div style={{display: 'flex', flexWrap: 'wrap', columnGap: 30}}>
            {qWords.map((w, i) => {
              const s = interpolate(t - qAt - 0.15 - i * 0.12, [0, 0.3], [0, 1], {...clamp, easing: ease});
              const last = i >= qWords.length - 2;
              return <span key={i} style={{fontFamily: FONT, fontWeight: 900, fontSize: 124, lineHeight: 1.12, whiteSpace: 'nowrap', color: last ? C.red : C.ink,
                opacity: s, transform: `translateY(${(1 - s) * 40}px)`, display: 'inline-block'}}>{w}</span>;
            })}
          </div>
          {sub ? <div style={{alignSelf: 'flex-start', padding: '16px 30px', borderRadius: 18, background: '#7C6CFF14', border: '2px solid #7C6CFF',
            fontFamily: FONT, fontWeight: 800, fontSize: 54, color: '#4B3FD1',
            opacity: interpolate(t, [sAt, sAt + 0.35], [0, 1], clamp), transform: `translateY(${interpolate(t, [sAt, sAt + 0.35], [24, 0], clamp)}px)`}}>{sub}</div> : null}
        </div>
      </div> : null}
    </AbsoluteFill>
  );
};
