import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {AccentCtx, tone, C, FONT, useFonts} from './ui';

// Ảnh bìa YouTube 1280×720, bản "viral sạch" Trọng chốt 26/11 (rút từ các thumbnail tài chính viral 12x đến 75x):
//   1 con số làm nhân vật chính, chữ ít (câu hỏi ngắn, viết thường có dấu, không IN HOA cả câu), nhãn vàng nổi,
//   so sánh 2 phía / trước sau, chủ thể lớn (logo dự án hoặc avatar penguin) thay cho khuôn mặt.
//   Vẫn giữ phong cách sạch của kênh: nền sáng có lưới nhạt, Be Vietnam Pro, thẻ trắng bo góc, lề 64px, không viền chữ.
// Bố cục: stat (số khủng + câu hỏi), pill (nhãn vàng lớn), vs (đối đầu 2 thẻ), before (trước → sau), question (câu hỏi + penguin).
// Python (insight_publish.thumb_style) chọn theo dữ liệu kịch bản, kịch bản có thể chỉ định thumb_style.
export type ThumbStyle = 'stat' | 'pill' | 'vs' | 'before' | 'question';
export type ThumbIcon = 'crack' | 'down' | 'up' | 'magnifier' | 'hourglass' | 'flame' | 'tape' | 'scale' | 'none';
type Side = {label: string; value: string; logo?: string | null; tone?: string};
export type ThumbProps = {text: string; stat?: string; accent?: string; projectLogo?: string | null; bg?: string | null; brand: string; points?: string[]; warn?: boolean;
  vs?: Side[]; font?: string; tag?: string; style?: ThumbStyle | string; icon?: ThumbIcon; kicker?: string; before?: Side | null; after?: Side | null};

const RED = '#E5383B', GREEN = '#1F9D63', AMBER = '#F4B400', YEL = '#FFD84D', IND = '#4F5BD5', INK = '#141833', MUTED = '#5A6080';

// ---------- hình dán tự vẽ (SVG), không dùng ảnh có bản quyền ----------
const Icon: React.FC<{kind: ThumbIcon; size: number; color: string}> = ({kind, size, color}) => {
  const s = size;
  const stroke = {stroke: C.ink, strokeWidth: s * 0.035, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const};
  switch (kind) {
    case 'crack':   // bong bóng nứt vỡ
      return <svg width={s} height={s} viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="40" fill={`${color}22`} stroke={color} strokeWidth="5" />
        <ellipse cx="36" cy="34" rx="9" ry="5" fill="#FFFFFF" opacity="0.9" transform="rotate(-35 36 34)" />
        <path d="M50 10 L46 30 L58 40 L44 55 L56 66 L50 90" fill="none" stroke={RED} strokeWidth="5" strokeLinejoin="round" />
        <path d="M58 40 L74 36 M44 55 L28 60" fill="none" stroke={RED} strokeWidth="4" />
        <path d="M86 18 l6 -4 M90 30 l7 1 M14 80 l-6 5" stroke={color} strokeWidth="4" strokeLinecap="round" />
      </svg>;
    case 'down':
      return <svg width={s} height={s} viewBox="0 0 100 100">
        <path d="M8 22 L36 48 L52 36 L86 76" fill="none" stroke={RED} strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M66 78 L90 80 L88 56" fill="none" stroke={RED} strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" />
      </svg>;
    case 'up':
      return <svg width={s} height={s} viewBox="0 0 100 100">
        <path d="M8 78 L36 52 L52 64 L86 24" fill="none" stroke={GREEN} strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M66 22 L90 20 L88 44" fill="none" stroke={GREEN} strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" />
      </svg>;
    case 'magnifier':
      return <svg width={s} height={s} viewBox="0 0 100 100">
        <circle cx="42" cy="42" r="26" fill="#FFFFFF" {...stroke} strokeWidth={7} />
        <path d="M61 61 L86 86" {...stroke} strokeWidth={12} />
        <path d="M30 40 q12 -14 24 0" fill="none" stroke={color} strokeWidth="5" strokeLinecap="round" />
      </svg>;
    case 'hourglass':
      return <svg width={s} height={s} viewBox="0 0 100 100">
        <path d="M26 12 H74 M26 88 H74" {...stroke} strokeWidth={7} />
        <path d="M30 14 C30 40 50 44 50 50 C50 56 30 60 30 86 H70 C70 60 50 56 50 50 C50 44 70 40 70 14 Z" fill="#FFFFFF" {...stroke} strokeWidth={5} />
        <path d="M38 80 H62 L50 66 Z M40 26 H60 L50 40 Z" fill={AMBER} />
      </svg>;
    case 'flame':
      return <svg width={s} height={s} viewBox="0 0 100 100">
        <path d="M50 8 C58 30 80 38 76 64 C73 84 58 92 50 92 C38 92 22 82 24 62 C26 46 38 40 40 26 C46 34 46 40 46 46 C54 38 54 22 50 8 Z" fill="#FF7A1A" />
        <path d="M50 52 C56 62 64 66 60 78 C57 86 44 86 41 78 C38 68 46 64 50 52 Z" fill={AMBER} />
      </svg>;
    case 'scale':
      return <svg width={s} height={s} viewBox="0 0 100 100">
        <path d="M50 14 V84 M30 86 H70 M18 30 H82" {...stroke} strokeWidth={6} />
        <path d="M18 30 L8 56 H28 Z M82 30 L72 56 H92 Z" fill={`${color}33`} {...stroke} strokeWidth={4} />
      </svg>;
    default:
      return null;
  }
};

// Hình dán: icon trong khối trắng viền dày, xoay nhẹ, bóng đổ (kiểu sticker), thay cho dấu "!" đỏ cũ
export const Sticker: React.FC<{kind: ThumbIcon; size: number; color: string; rotate?: number}> = ({kind, size, color, rotate = -8}) => (
  <div style={{width: size, height: size, borderRadius: size * 0.28, background: '#FFFFFF', border: `${size * 0.035}px solid #FFFFFF`,
    boxShadow: `0 0 0 ${size * 0.02}px ${C.line}, 0 ${size * 0.08}px ${size * 0.2}px rgba(40,50,110,0.22)`, transform: `rotate(${rotate}deg)`,
    display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
    <Icon kind={kind} size={size * 0.78} color={color} />
  </div>
);

const valueColor = (v: string) => (/^\s*[-−]/.test(v) ? RED : /^\s*\+/.test(v) ? GREEN : INK);
const sideColor = (x: Side) => (x.tone === 'down' ? RED : x.tone === 'up' ? GREEN : valueColor(x.value));
// cỡ chữ tự co theo độ dài để không bao giờ tràn khung (BVP ExtraBold rộng khoảng 0.6em mỗi ký tự)
const fit = (t: string, maxW: number, maxSize: number, em = 0.6) => Math.round(Math.min(maxSize, maxW / Math.max(1, (t || '').length * em)));
const nb = (t: string) => (t || '').replace(/_/g, ' ');   // dấu _ dính các chữ thành 1 cụm không bị ngắt dòng

const card: React.CSSProperties = {background: '#FFFFFF', borderRadius: 32, boxShadow: '0 24px 60px rgba(20,24,51,0.12), 0 2px 6px rgba(20,24,51,0.05)'};
const pill = (bg: string, color: string, size: number): React.CSSProperties => ({display: 'inline-block', background: bg, color, fontSize: size, fontWeight: 800,
  padding: `${Math.round(size * 0.2)}px ${Math.round(size * 0.55)}px`, borderRadius: Math.round(size * 0.32), whiteSpace: 'nowrap', lineHeight: 1.2});
const big: React.CSSProperties = {fontWeight: 800, letterSpacing: '-0.04em', lineHeight: 1, whiteSpace: 'nowrap'};

const Hero: React.FC<{src?: string | null; size: number; accent: string}> = ({src, size, accent}) => (
  <div style={{width: size, height: size, borderRadius: '50%', overflow: 'hidden', border: '12px solid #FFFFFF', background: src ? '#FFFFFF' : '#A9CBF2',
    boxShadow: `0 24px 60px rgba(20,24,51,0.18), 0 0 0 2px ${accent}22`, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
    <Img src={staticFile(src || 'logo.png')} style={src ? {width: '78%', height: '78%', objectFit: 'contain', borderRadius: '50%'} : {width: '100%', height: '100%'}} />
  </div>
);
const Brand: React.FC<{brand: string; center?: boolean; right?: number}> = ({brand, center, right}) => (
  <div style={{position: 'absolute', bottom: 40, ...(center ? {left: 0, right: 0, justifyContent: 'center'} : right !== undefined ? {right} : {left: 64}),
    display: 'flex', alignItems: 'center', gap: 12, fontSize: 24, fontWeight: 700, color: MUTED}}>
    <Img src={staticFile('logo.png')} style={{width: 46, height: 46, borderRadius: 99, border: '3px solid #FFFFFF', boxShadow: '0 4px 12px rgba(20,24,51,0.15)'}} />{brand}
  </div>
);
const Curve: React.FC<{w: number; h: number; color: string; down?: boolean}> = ({w, h, color, down}) => {
  const d = down ? `M0 ${h * 0.05} C ${w * 0.35} ${h * 0.08}, ${w * 0.6} ${h * 0.3}, ${w * 0.75} ${h * 0.55} S ${w * 0.93} ${h * 0.9}, ${w} ${h * 0.95}`
    : `M0 ${h * 0.95} C ${w * 0.35} ${h * 0.93}, ${w * 0.6} ${h * 0.77}, ${w * 0.75} ${h * 0.5} S ${w * 0.93} ${h * 0.14}, ${w} ${h * 0.05}`;
  return <svg width={w} height={h} style={{position: 'absolute', left: 0, bottom: 0}}>
    <defs><linearGradient id="cv" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={color} stopOpacity="0.25" /><stop offset="1" stopColor={color} stopOpacity="0" /></linearGradient></defs>
    <path d={`${d} L${w} ${h} L0 ${h}Z`} fill="url(#cv)" /><path d={d} fill="none" stroke={color} strokeWidth={10} />
  </svg>;
};

export const Thumb: React.FC<ThumbProps> = ({text, stat = '', accent: acIn = IND, projectLogo, brand, points = [], vs = [], tag = '',
  style: styleIn, kicker = '', before, after, icon = 'none'}) => {
  const accent = tone(acIn);
  useFonts();
  const t = nb(text), k = nb(kicker), g = nb(tag);
  const style: ThumbStyle = (['stat', 'pill', 'vs', 'before', 'question'] as string[]).includes(String(styleIn)) ? styleIn as ThumbStyle
    : before && after ? 'before' : vs.length >= 2 ? 'vs' : stat ? 'stat' : 'question';
  const q = /\?\s*$/.test(t);
  // Trọng 26/11 (ghi nhớ bằng code): chủ đề khớp hình dán thì phải có hình dán; nhắc dự án thì có logo (Hero / projectLogo).
  const stk = icon && icon !== 'none' ? icon : null;
  const StickerAt = (pos: React.CSSProperties, size: number, rot = -10) => stk
    ? <div style={{position: 'absolute', ...pos}}><Sticker kind={stk} size={size} color={accent} rotate={rot} /></div> : null;
  let body: React.ReactNode = null;

  if (style === 'stat') {
    // số khủng bên trái, câu hỏi trong nhãn tím, chủ thể tròn lớn bên phải (mẫu "-$6T, cú rũ hay sụp đổ?")
    body = <>
      {k ? <div style={{position: 'absolute', left: 64, top: 64, fontSize: 40, fontWeight: 700, color: MUTED, whiteSpace: 'nowrap'}}>{k}</div> : null}
      {g ? <div style={{position: 'absolute', left: 64, top: k ? 124 : 70}}><span style={pill(RED, '#FFFFFF', 34)}>{g}</span></div> : null}
      <div style={{position: 'absolute', left: 58, top: 206, ...big, fontSize: fit(stat, 640, 230, 0.58), color: valueColor(stat) === INK ? INK : valueColor(stat)}}>{nb(stat)}</div>
      <div style={{position: 'absolute', left: 64, top: 470, width: 660}}>{t.length > 24
        ? <div style={{...pill(IND, '#FFFFFF', 44), whiteSpace: 'normal', lineHeight: 1.25}}>{t}</div>
        : <span style={pill(IND, '#FFFFFF', fit(t, 640, 54, 0.62))}>{t}</span>}</div>
      <div style={{position: 'absolute', right: 96, top: 120}}><Hero src={projectLogo} size={420} accent={accent} /></div>
      {StickerAt({right: 420, top: 420}, 150, -10)}
      {q ? <div style={{position: 'absolute', right: 64, top: 96, width: 110, height: 110, borderRadius: 99, background: YEL, fontSize: 72, fontWeight: 800,
        display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 12px 30px rgba(20,24,51,0.15)'}}>?</div> : null}
      <Brand brand={brand} />
    </>;
  } else if (style === 'pill') {
    // nhãn vàng cỡ lớn giữa khung, các ý thành thẻ nhỏ phía trên, số khủng góc phải (mẫu "Bong bóng AI vỡ?")
    const chips = points.slice(0, 3);
    body = <>
      <div style={{position: 'absolute', left: 64, top: 64, display: 'flex', gap: 22}}>
        {chips.map((p, i) => <div key={i} style={{...card, borderRadius: 24, padding: '22px 26px', minWidth: 170, textAlign: 'center',
          fontSize: fit(p, 200, 38, 0.6), fontWeight: 800, color: INK, whiteSpace: 'nowrap'}}>{nb(p)}</div>)}
      </div>
      {stat ? <div style={{position: 'absolute', right: 64, top: 70, ...big, fontSize: fit(stat, chips.length ? 1150 - chips.length * 240 - 90 : 700, 190, 0.58),
        color: valueColor(stat) === INK ? RED : valueColor(stat)}}>{nb(stat)}</div> : null}
      <div style={{position: 'absolute', left: 0, right: 0, top: 320, textAlign: 'center'}}>
        <span style={{...pill(YEL, INK, fit(t, 1050, 116, 0.6)), letterSpacing: '-0.03em', borderRadius: 30, boxShadow: '0 20px 50px rgba(20,24,51,0.15)'}}>{t}</span></div>
      {projectLogo ? <div style={{position: 'absolute', right: 64, top: 500}}><Hero src={projectLogo} size={130} accent={accent} /></div>
        : StickerAt({right: 64, top: 500}, 130, 8)}
      {k ? <div style={{position: 'absolute', right: 230, bottom: 44, fontSize: 28, fontWeight: 700, color: MUTED, whiteSpace: 'nowrap'}}>{k}</div> : null}
      <Brand brand={brand} />
    </>;
  } else if (style === 'vs') {
    // đối đầu: 2 thẻ lớn logo + số, vòng VS vàng ở giữa, tiêu đề có nhãn đỏ (mẫu "Coin tốt vẫn lỗ?")
    const [a, b] = vs;
    const sideCard = (x: Side, pos: React.CSSProperties) => (
      <div style={{position: 'absolute', top: 180, width: 470, height: 420, ...card, textAlign: 'center', paddingTop: 44, ...pos}}>
        {x.logo ? <Img src={staticFile(x.logo)} style={{width: 170, height: 170, borderRadius: 99, boxShadow: '0 18px 40px rgba(20,24,51,0.18)'}} />
          : <div style={{height: 170, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 72, fontWeight: 800, color: INK}}>{nb(x.label)}</div>}
        <div style={{fontSize: 34, fontWeight: 700, color: MUTED, marginTop: 16, whiteSpace: 'nowrap'}}>{nb(x.label)}{k ? ` · ${k}` : ''}</div>
        <div style={{...big, fontSize: fit(x.value, 420, 120, 0.6), color: sideColor(x), marginTop: 8}}>{nb(x.value)}</div>
      </div>);
    body = <>
      <div style={{position: 'absolute', left: 0, right: 0, top: 50, textAlign: 'center', fontSize: fit(t + g, 1100, 84, 0.62), fontWeight: 800, letterSpacing: '-0.02em', whiteSpace: 'nowrap'}}>
        {t}{g ? <> <span style={{...pill(RED, '#FFFFFF', fit(t + g, 1100, 84, 0.62)), padding: '0 24px'}}>{g}</span></> : null}</div>
      {sideCard(a, {left: 110})}
      {sideCard(b, {right: 110})}
      <div style={{position: 'absolute', left: 590, top: 342, width: 100, height: 100, borderRadius: 99, background: YEL, fontSize: 38, fontWeight: 800,
        display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 12px 30px rgba(20,24,51,0.18)'}}>VS</div>
      <Brand brand={brand} center />
    </>;
  } else if (style === 'before') {
    // trước → sau: thẻ nhỏ bên trái, thẻ lớn có đường tăng/giảm bên phải, nhãn vàng dưới (mẫu "$10K → $1.6M")
    const b0 = before as Side, a0 = after as Side, col = valueColor(a0.value) === RED || a0.tone === 'down' ? RED : GREEN;
    body = <>
      <div style={{position: 'absolute', left: 64, top: 150, width: 330, height: 300, ...card, textAlign: 'center', paddingTop: 44}}>
        <div style={{fontSize: 30, fontWeight: 700, color: MUTED, whiteSpace: 'nowrap'}}>{nb(b0.label)}</div>
        <div style={{...big, fontSize: fit(b0.value, 290, 118, 0.6), color: INK, marginTop: 20}}>{nb(b0.value)}</div>
      </div>
      <svg style={{position: 'absolute', left: 418, top: 250}} width="150" height="100"><path d="M10 50 H125 M95 18 L132 50 L95 82" fill="none" stroke={INK}
        strokeWidth="14" strokeLinecap="round" strokeLinejoin="round" /></svg>
      <div style={{position: 'absolute', left: 592, top: 64, width: 624, height: 470, ...card, overflow: 'hidden'}}>
        <div style={{position: 'absolute', left: 44, top: 40, fontSize: 30, fontWeight: 700, color: MUTED, whiteSpace: 'nowrap'}}>{nb(a0.label)}</div>
        <div style={{position: 'absolute', left: 38, top: 84, ...big, fontSize: fit(a0.value, 550, 170, 0.6), color: col}}>{nb(a0.value)}</div>
        <Curve w={624} h={220} color={col} down={col === RED} />
      </div>
      {t ? <div style={{position: 'absolute', left: 64, top: 560}}><span style={pill(YEL, INK, fit(t, 900, 44, 0.6))}>{t}</span></div> : null}
      {projectLogo ? <Img src={staticFile(projectLogo)} style={{position: 'absolute', right: 64, top: 566, height: 84, maxWidth: 220, objectFit: 'contain'}} />
        : stk ? StickerAt({right: 64, top: 556}, 120, 8) : <Brand brand={brand} right={64} />}
    </>;
  } else {
    // question: câu hỏi/khẳng định lớn bên trái, nhãn vàng, chủ thể tròn bên phải (mẫu "Nếu bắt đầu lại từ $0")
    const main = stat || t, sub = stat ? t : '';
    body = <>
      {k ? <div style={{position: 'absolute', left: 64, top: 80, fontSize: fit(k, 640, 60, 0.58), fontWeight: 700, color: MUTED, whiteSpace: 'nowrap'}}>{k}</div> : null}
      <div style={{position: 'absolute', left: 58, top: 160, ...big, fontSize: fit(main, 660, 230, 0.6), color: stat ? valueColor(stat) : INK}}>{nb(main)}</div>
      {sub ? <div style={{position: 'absolute', left: 64, top: 392, fontSize: fit(sub, 640, 72, 0.6), fontWeight: 800, letterSpacing: '-0.02em', whiteSpace: 'nowrap'}}>{sub}</div> : null}
      {g ? <div style={{position: 'absolute', left: 64, top: sub ? 482 : 420}}><span style={{...pill(YEL, INK, fit(g, 640, sub ? 76 : 84, 0.6)), letterSpacing: '-0.03em'}}>{g}</span></div> : null}
      {vs.length ? <div style={{position: 'absolute', right: 64, top: 90, width: 420, ...card, padding: '34px 38px'}}>
        {vs.slice(0, 2).map((x, i) => <div key={i} style={{display: 'flex', alignItems: 'center', gap: 22, marginTop: i ? 26 : 0, paddingTop: i ? 26 : 0,
          borderTop: i ? '2px solid #EEF0F7' : 'none'}}>
          {x.logo ? <Img src={staticFile(x.logo)} style={{width: 96, height: 96, borderRadius: 99}} /> : <div style={{fontSize: 40, fontWeight: 800}}>{nb(x.label)}</div>}
          <span style={{...big, fontSize: fit(x.value, 250, 76, 0.6), color: sideColor(x)}}>{nb(x.value)}</span></div>)}
      </div> : <><div style={{position: 'absolute', right: 110, top: 110}}><Hero src={projectLogo} size={400} accent={accent} /></div>
        {StickerAt({right: 64, top: 400}, 150, 10)}</>}
      <Brand brand={brand} right={vs.length ? 64 : undefined} />
    </>;
  }
  return (
    <AccentCtx.Provider value={accent}>
      <AbsoluteFill style={{fontFamily: FONT, fontWeight: 800, color: INK, overflow: 'hidden',
        background: `radial-gradient(ellipse 60% 70% at 85% 30%, ${accent}21, transparent 70%), #F6F7FC`}}>
        <AbsoluteFill style={{backgroundImage: 'linear-gradient(rgba(79,91,213,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(79,91,213,0.06) 1px, transparent 1px)',
          backgroundSize: '64px 64px'}} />
        {body}
      </AbsoluteFill>
    </AccentCtx.Provider>
  );
};
