import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {AccentCtx, tone, C, FONT, DISPLAY_FONT, useFonts} from './ui';

// Ảnh bìa YouTube 1280×720: chữ to, 1 con số, logo dự án + logo kênh
export type ThumbProps = {text: string; stat?: string; accent?: string; projectLogo?: string | null; bg?: string | null; brand: string; points?: string[]; warn?: boolean;
  vs?: {label: string; value: string; logo?: string | null; tone?: string}[]; font?: string};
export const Thumb: React.FC<ThumbProps> = ({text, stat, accent: acIn = '#4F5BD5', projectLogo, bg, brand, points = [], warn = false, vs = [], font = 'bvp'}) => {
  const HF = DISPLAY_FONT[font] || FONT;
  const cond = font === 'anton' || font === 'barlow' || font === 'archivo';
  const accent = tone(acIn);
  useFonts();
  const words = (text || '').toUpperCase().split(/\s+/);
  return (
    <AccentCtx.Provider value={accent}>
      <AbsoluteFill style={{background: C.bg, fontFamily: FONT}}>
        {bg ? <Img src={staticFile(bg)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: 0.35, filter: 'saturate(0.8)'}} /> : null}
        <AbsoluteFill style={{background: `radial-gradient(900px 600px at 15% 20%, ${accent}40, transparent 70%), linear-gradient(90deg, ${C.bg} 35%, rgba(243,245,251,0.4))`}} />
        <div style={{position: 'absolute', left: 64, top: 48, display: 'flex', alignItems: 'center', gap: 14}}>
          <Img src={staticFile('logo.png')} style={{width: 64, height: 64, borderRadius: 99}} />
          <div style={{color: C.ink, fontWeight: 800, fontSize: 26, letterSpacing: 2}}>{brand.toUpperCase()}</div>
        </div>
        <div style={{position: 'absolute', left: 64, top: 160, width: points.length ? 740 : 1080, display: 'flex', flexWrap: 'wrap', columnGap: 22,
          fontFamily: HF, fontStretch: font === 'archivo' ? '62%' : undefined, fontWeight: font === 'anton' ? 400 : 900,
          // Trọng 22/11: chữ to quá bị mất dấu (dấu mũ + ngã chồng lên dòng trên). Cỡ vừa phải, giãn dòng đủ cho chữ hoa có 2 tầng dấu
          fontSize: (points.length ? 64 : words.join(' ').length > 28 ? 72 : words.join(' ').length > 18 ? 84 : 96) * (cond ? 1.2 : 1),
          lineHeight: 1.32, rowGap: 6, ...(vs.length ? {fontSize: 112} : {}), color: C.ink, letterSpacing: 0}}>
          {words.map((w, i) => <span key={i} style={{color: i % 3 === 1 ? accent : C.ink}}>{w}</span>)}
        </div>
        {vs.length ? <div style={{position: 'absolute', left: 64, right: 64, top: 330, display: 'flex', alignItems: 'center', gap: 20}}>
          {vs.map((x, i) => <React.Fragment key={i}>
            {i ? <div style={{fontWeight: 800, fontSize: 40, color: C.muted, flexShrink: 0}}>VS</div> : null}
            <div style={{flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', gap: 18, padding: '22px 26px', borderRadius: 26,
            background: '#FFFFFF', border: `1px solid ${C.line}`, boxShadow: '0 14px 40px rgba(40,50,110,0.14)'}}>
            {x.logo ? <Img src={staticFile(x.logo)} style={{width: 88, height: 88, borderRadius: 99, flexShrink: 0}} /> : null}
            <div style={{fontWeight: 800, fontSize: 40, color: C.ink}}>{x.label}</div>
            <div style={{flex: 1}} />
            <div style={{fontFamily: HF, fontStretch: font === 'archivo' ? '62%' : undefined, fontWeight: font === 'anton' ? 400 : 900,
              fontSize: cond ? 96 : 80, color: x.tone === 'down' ? C.red : x.tone === 'up' ? C.green : C.ink, whiteSpace: 'nowrap'}}>{x.value}</div>
          </div></React.Fragment>)}
        </div> : null}
        {vs.length ? <div style={{position: 'absolute', left: 64, top: 520, color: C.muted, fontWeight: 700, fontSize: 30}}>Từ đầu năm 2026 · 4 câu hỏi trước khi mua</div> : null}
        {stat && !vs.length ? <div style={{position: 'absolute', left: 64, bottom: 60, padding: '10px 30px', borderRadius: 20, background: accent,
          color: '#FFFFFF', fontWeight: 800, fontSize: 92, lineHeight: 1.1}}>{stat}</div> : null}
        {points.length ? <div style={{position: 'absolute', right: 56, top: 170, width: 400, padding: '30px 30px', borderRadius: 26,
          background: '#FFFFFF', border: `1px solid ${C.line}`, boxShadow: '0 18px 50px rgba(40,50,110,0.12)', display: 'flex', flexDirection: 'column', gap: 22}}>
          {points.map((p, i) => <div key={i} style={{display: 'flex', alignItems: 'center', gap: 16}}>
            <div style={{width: 44, height: 44, borderRadius: 12, background: accent, color: '#FFFFFF', fontSize: 30, fontWeight: 800,
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>✓</div>
            <div style={{color: C.ink, fontWeight: 700, fontSize: 30, lineHeight: 1.15}}>{p}</div>
          </div>)}
        </div> : null}
        {projectLogo && !points.length ? <Img src={staticFile(projectLogo)} style={{position: 'absolute', right: 110, top: 200, width: 300, height: 300, borderRadius: '50%',
          boxShadow: `0 0 0 10px ${accent}55, 0 18px 50px rgba(40,50,110,0.15)`}} /> : null}
        {/* review 1518: thêm điểm nhìn gây tò mò, biểu tượng cảnh báo đỏ */}
        {warn ? <div style={{position: 'absolute', right: points.length ? 420 : 60, top: points.length ? 120 : 60, width: 104, height: 104, borderRadius: 99,
          background: '#E5383B', color: '#FFFFFF', fontSize: 72, fontWeight: 900, display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 0 0 8px rgba(229,56,59,0.22), 0 14px 34px rgba(229,56,59,0.35)', transform: 'rotate(-8deg)'}}>!</div> : null}
        <div style={{position: 'absolute', right: 40, bottom: 30, color: 'rgba(19,24,54,0.7)', fontWeight: 700, fontSize: 28}}>@Trong0322</div>
      </AbsoluteFill>
    </AccentCtx.Provider>
  );
};
