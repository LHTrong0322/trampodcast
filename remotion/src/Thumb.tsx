import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {AccentCtx, tone, C, FONT, DISPLAY_FONT, useFonts} from './ui';

// Ảnh bìa YouTube 1280×720.
// Trọng 22/11: "ảnh bìa hãy thêm sự sáng tạo, đừng rập khuôn như nhau, cả cái biển báo đỏ cũng phải làm khác đi".
// → Nhiều bố cục (style) và bộ hình dán theo chủ đề (icon), Python chọn theo nội dung + xoay vòng để 2 video liền nhau không giống nhau.
//   Nền luôn sáng sạch (Trọng 22/11), không thẻ nền màu đậm.
export type ThumbStyle = 'classic' | 'hero' | 'sticker' | 'stack' | 'vs';
export type ThumbIcon = 'crack' | 'down' | 'up' | 'magnifier' | 'hourglass' | 'flame' | 'tape' | 'scale' | 'none';
export type ThumbProps = {text: string; stat?: string; accent?: string; projectLogo?: string | null; bg?: string | null; brand: string; points?: string[]; warn?: boolean;
  vs?: {label: string; value: string; logo?: string | null; tone?: string}[]; font?: string; tag?: string; style?: ThumbStyle; icon?: ThumbIcon};

const RED = '#E5383B', GREEN = '#1F9D63', AMBER = '#F4B400';

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
const Sticker: React.FC<{kind: ThumbIcon; size: number; color: string; rotate?: number}> = ({kind, size, color, rotate = -8}) => (
  <div style={{width: size, height: size, borderRadius: size * 0.28, background: '#FFFFFF', border: `${size * 0.035}px solid #FFFFFF`,
    boxShadow: `0 0 0 ${size * 0.02}px ${C.line}, 0 ${size * 0.08}px ${size * 0.2}px rgba(40,50,110,0.22)`, transform: `rotate(${rotate}deg)`,
    display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
    <Icon kind={kind} size={size * 0.78} color={color} />
  </div>
);

// Băng cảnh báo vàng đen chéo góc (thay biển "!" đỏ khi kịch bản cần cảnh báo)
const Tape: React.FC<{text: string}> = ({text}) => (
  <div style={{position: 'absolute', right: -120, top: 70, width: 560, transform: 'rotate(32deg)', padding: '12px 0', textAlign: 'center',
    background: `repeating-linear-gradient(45deg, ${AMBER} 0 26px, #1A1A1A 26px 52px)`, boxShadow: '0 10px 26px rgba(0,0,0,0.25)'}}>
    <span style={{background: AMBER, padding: '4px 18px', fontWeight: 900, fontSize: 30, color: '#1A1A1A', letterSpacing: 2}}>{text}</span>
  </div>
);

const valueColor = (v: string) => (/^\s*[-−]/.test(v) ? RED : /^\s*\+/.test(v) ? GREEN : C.ink);

export const Thumb: React.FC<ThumbProps> = ({text, stat, accent: acIn = '#4F5BD5', projectLogo, bg, brand, points = [], warn = false, vs = [],
  font = 'bvp', tag = '', style: styleIn, icon = 'none'}) => {
  const HF = DISPLAY_FONT[font] || FONT;
  const cond = font === 'anton' || font === 'barlow' || font === 'archivo';
  const disp = {fontFamily: HF, fontStretch: font === 'archivo' ? '62%' : undefined, fontWeight: font === 'anton' ? 400 : 900} as const;
  const accent = tone(acIn);
  useFonts();
  const style: ThumbStyle = styleIn || (vs.length ? 'vs' : 'classic');
  const words = (text || '').toUpperCase().split(/\s+/).filter(Boolean);
  const len = words.join(' ').length;
  const hl = (i: number) => (style === 'stack' ? C.ink : i % 3 === 1 ? accent : C.ink);
  const brandRow = (
    <div style={{position: 'absolute', left: 64, top: 44, display: 'flex', alignItems: 'center', gap: 14}}>
      <Img src={staticFile('logo.png')} style={{width: 60, height: 60, borderRadius: 99}} />
      <div style={{color: C.ink, fontWeight: 800, fontSize: 24, letterSpacing: 2}}>{brand.toUpperCase()}</div>
    </div>
  );
  const bgLayer = (
    <>
      {bg ? <Img src={staticFile(bg)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: 0.3, filter: 'saturate(0.8)'}} /> : null}
      <AbsoluteFill style={{background: style === 'hero'
        ? `radial-gradient(700px 520px at 88% 70%, ${accent}33, transparent 70%), radial-gradient(600px 400px at 8% 10%, ${accent}22, transparent 70%)`
        : style === 'sticker' ? `radial-gradient(620px 520px at 80% 45%, ${accent}2E, transparent 70%)`
        : `radial-gradient(900px 600px at 15% 20%, ${accent}40, transparent 70%), linear-gradient(90deg, ${C.bg} 35%, rgba(243,245,251,0.4))`}} />
      {/* vân lưới nhẹ cho đỡ trơn */}
      <AbsoluteFill style={{backgroundImage: `radial-gradient(${accent}22 2px, transparent 2px)`, backgroundSize: '34px 34px', opacity: 0.5,
        maskImage: 'linear-gradient(90deg, transparent 40%, black)', WebkitMaskImage: 'linear-gradient(90deg, transparent 40%, black)'}} />
    </>
  );
  const handle = <div style={{position: 'absolute', right: 40, bottom: 28, color: 'rgba(19,24,54,0.7)', fontWeight: 700, fontSize: 26}}>@Trong0322</div>;

  // ---------- bố cục ----------
  let body: React.ReactNode = null;
  if (style === 'hero') {
    // con số khổng lồ là nhân vật chính, tiêu đề gọn phía trên
    body = <>
      <div style={{position: 'absolute', left: 64, top: 130, width: 760, display: 'flex', flexWrap: 'wrap', columnGap: 18, ...disp,
        fontSize: (len > 22 ? 70 : 84) * (cond ? 1.2 : 1), lineHeight: 1.3, color: C.ink}}>
        {words.map((w, i) => <span key={i} style={{color: hl(i)}}>{w}</span>)}
      </div>
      {icon !== 'none' ? <div style={{position: 'absolute', right: warn ? 110 : 70, top: warn ? 215 : 120, opacity: 0.95}}><Sticker kind={icon} size={190} color={accent} rotate={10} /></div> : null}
      {stat ? <div style={{position: 'absolute', left: 56, bottom: 54, ...disp, fontSize: (stat.length > 6 ? 190 : 230) * (cond ? 1.15 : 1), lineHeight: 1,
        color: valueColor(stat), letterSpacing: -4, textShadow: '0 8px 0 rgba(19,24,54,0.08)'}}>{stat}</div> : null}
      {tag ? <div style={{position: 'absolute', right: 64, bottom: 90, padding: '12px 24px', borderRadius: 14, background: '#FFFFFF', border: `3px solid ${accent}`,
        color: accent, fontWeight: 900, fontSize: 36, transform: 'rotate(-4deg)', boxShadow: '0 10px 24px rgba(40,50,110,0.14)'}}>{tag.toUpperCase()}</div> : null}
    </>;
  } else if (style === 'sticker') {
    // hình dán to bên phải kể câu chuyện, chữ bên trái; số liệu như mác giá treo dưới hình dán
    body = <>
      <div style={{position: 'absolute', left: 64, top: 150, width: 700, display: 'flex', flexWrap: 'wrap', columnGap: 20, ...disp,
        fontSize: (len > 28 ? 72 : len > 18 ? 86 : 100) * (cond ? 1.2 : 1), lineHeight: 1.3, color: C.ink}}>
        {words.map((w, i) => <span key={i} style={{color: hl(i)}}>{w}</span>)}
      </div>
      <div style={{position: 'absolute', right: warn ? 150 : 120, top: warn ? 165 : 120}}><Sticker kind={icon === 'none' ? 'magnifier' : icon} size={warn ? 290 : 330} color={accent} rotate={-9} /></div>
      {stat ? <div style={{position: 'absolute', right: 96, top: warn ? 490 : 470, padding: '8px 30px 8px 52px', background: '#FFFFFF', borderRadius: '14px 40px 40px 14px',
        border: `4px solid ${C.ink}`, ...disp, fontSize: 76 * (cond ? 1.15 : 1), color: valueColor(stat), transform: 'rotate(6deg)',
        boxShadow: '0 12px 30px rgba(40,50,110,0.18)'}}>
        <span style={{position: 'absolute', left: 16, top: '50%', width: 18, height: 18, marginTop: -9, borderRadius: 99, background: C.bg, border: `3px solid ${C.ink}`}} />
        {stat}</div> : null}
      {tag ? <div style={{position: 'absolute', left: 64, bottom: 70, padding: '10px 24px', borderRadius: 12, background: `${accent}18`, border: `2px solid ${accent}`,
        color: accent, fontWeight: 800, fontSize: 34}}>{tag.toUpperCase()}</div> : null}
    </>;
  } else if (style === 'stack') {
    // tiêu đề tô dạ quang từng dòng + các ý thành nhãn số dưới đáy
    const lines: string[][] = [];
    words.forEach((w) => { const L = lines[lines.length - 1]; if (!L || L.join(' ').length + w.length > 14) lines.push([w]); else L.push(w); });
    body = <>
      <div style={{position: 'absolute', left: 64, top: 140, display: 'flex', flexDirection: 'column', gap: 14}}>
        {lines.slice(0, 3).map((L, i) => <div key={i} style={{alignSelf: 'flex-start', ...disp, fontSize: 92 * (cond ? 1.15 : 1), lineHeight: 1.25, color: C.ink,
          padding: '0 18px', background: i === 1 ? `linear-gradient(transparent 52%, ${AMBER}AA 52%, ${AMBER}AA 92%, transparent 92%)` : 'none'}}>{L.join(' ')}</div>)}
      </div>
      {points.length ? <div style={{position: 'absolute', left: 64, right: 64, bottom: 70, display: 'flex', gap: 16}}>
        {points.map((p, i) => <div key={i} style={{flex: 1, display: 'flex', alignItems: 'center', gap: 12, padding: '14px 16px', borderRadius: 18, background: '#FFFFFF',
          border: `1px solid ${C.line}`, boxShadow: '0 10px 26px rgba(40,50,110,0.12)'}}>
          <div style={{width: 46, height: 46, borderRadius: 99, background: accent, color: '#FFFFFF', fontWeight: 900, fontSize: 28, display: 'flex',
            alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>{i + 1}</div>
          <div style={{fontWeight: 800, fontSize: 28, color: C.ink, lineHeight: 1.15}}>{p}</div></div>)}
      </div> : null}
      {icon !== 'none' ? <div style={{position: 'absolute', right: warn ? 120 : 80, top: warn ? 190 : 120}}><Sticker kind={icon} size={warn ? 190 : 230} color={accent} rotate={8} /></div> : null}
      {stat ? <div style={{position: 'absolute', right: 80, top: warn ? 400 : 380, ...disp, fontSize: 110, color: valueColor(stat)}}>{stat}</div> : null}
    </>;
  } else if (style === 'vs') {
    body = <>
      <div style={{position: 'absolute', left: 64, top: 190, display: 'flex', columnGap: 22, ...disp, fontSize: cond ? 118 : 100, whiteSpace: 'nowrap', lineHeight: 1.32, color: C.ink}}>
        {words.map((w, i) => <span key={i} style={{color: hl(i)}}>{w}</span>)}
      </div>
      <div style={{position: 'absolute', left: 64, right: 64, top: 400, display: 'flex', alignItems: 'center', gap: 18}}>
        {vs.map((x, i) => <React.Fragment key={i}>
          {i ? <div style={{fontWeight: 800, fontSize: 40, color: C.muted, flexShrink: 0}}>VS</div> : null}
          <div style={{flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', gap: 14, padding: '20px 22px', borderRadius: 26,
            background: '#FFFFFF', border: `1px solid ${C.line}`, boxShadow: '0 14px 40px rgba(40,50,110,0.14)'}}>
            {x.logo ? <Img src={staticFile(x.logo)} style={{width: 64, height: 64, borderRadius: 99, flexShrink: 0}} /> : null}
            <div style={{fontWeight: 800, fontSize: 32, color: C.ink}}>{x.label}</div>
            <div style={{flex: 1}} />
            <div style={{...disp, fontSize: cond ? 100 : 82, color: x.tone === 'down' ? RED : x.tone === 'up' ? GREEN : C.ink, whiteSpace: 'nowrap'}}>{x.value}</div>
          </div></React.Fragment>)}
      </div>
      {tag ? <div style={{position: 'absolute', left: 64, top: 574, padding: '12px 26px', borderRadius: 16, background: accent, color: '#FFFFFF', fontWeight: 800,
        fontSize: 38, letterSpacing: 1}}>{tag.toUpperCase()}</div> : null}
    </>;
  } else {
    // classic: chữ trái, danh sách tick hoặc logo dự án bên phải; số liệu và nhãn phụ xếp dọc, không đè nhau
    body = <>
      <div style={{position: 'absolute', left: 64, top: 150, width: points.length ? 720 : 1000, display: 'flex', flexWrap: 'wrap', columnGap: 22, ...disp,
        fontSize: (points.length ? 68 : len > 28 ? 72 : len > 18 ? 84 : 96) * (cond ? 1.2 : 1), lineHeight: 1.32, rowGap: 6, color: C.ink}}>
        {words.map((w, i) => <span key={i} style={{color: hl(i)}}>{w}</span>)}
      </div>
      {points.length ? <div style={{position: 'absolute', right: 56, top: 170, width: 410, padding: '30px 30px', borderRadius: 26,
        background: '#FFFFFF', border: `1px solid ${C.line}`, boxShadow: '0 18px 50px rgba(40,50,110,0.12)', display: 'flex', flexDirection: 'column', gap: 22}}>
        {points.map((p, i) => <div key={i} style={{display: 'flex', alignItems: 'center', gap: 16}}>
          <div style={{width: 44, height: 44, borderRadius: 12, background: accent, color: '#FFFFFF', fontSize: 30, fontWeight: 800,
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>✓</div>
          <div style={{color: C.ink, fontWeight: 700, fontSize: 30, lineHeight: 1.15}}>{p}</div>
        </div>)}
      </div> : projectLogo ? <Img src={staticFile(projectLogo)} style={{position: 'absolute', right: 110, top: 200, width: 300, height: 300, borderRadius: '50%',
        boxShadow: `0 0 0 10px ${accent}55, 0 18px 50px rgba(40,50,110,0.15)`}} /> : null}
      {icon !== 'none' && !points.length && !projectLogo ? <div style={{position: 'absolute', right: warn ? 160 : 110, top: warn ? 230 : 180}}><Sticker kind={icon} size={260} color={accent} rotate={-10} /></div> : null}
      <div style={{position: 'absolute', left: 64, bottom: 56, display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 14}}>
        {tag ? <div style={{padding: '10px 24px', borderRadius: 14, background: `${accent}18`, border: `2px solid ${accent}`, color: accent, fontWeight: 800, fontSize: 34}}>
          {tag.toUpperCase()}</div> : null}
        {stat ? <div style={{padding: '6px 28px', borderRadius: 20, background: '#FFFFFF', border: `4px solid ${valueColor(stat) === C.ink ? accent : valueColor(stat)}`,
          ...disp, fontSize: 92, lineHeight: 1.15, color: valueColor(stat) === C.ink ? accent : valueColor(stat)}}>{stat}</div> : null}
      </div>
    </>;
  }
  return (
    <AccentCtx.Provider value={accent}>
      <AbsoluteFill style={{background: C.bg, fontFamily: FONT, overflow: 'hidden'}}>
        {bgLayer}
        {brandRow}
        {body}
        {warn ? <Tape text="CẢNH BÁO" /> : null}
        {handle}
      </AbsoluteFill>
    </AccentCtx.Provider>
  );
};
