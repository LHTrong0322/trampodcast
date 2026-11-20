import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {AccentCtx, tone, C, FONT, useFonts} from './ui';

// Ảnh bìa YouTube 1280×720: chữ to, 1 con số, logo dự án + logo kênh
export type ThumbProps = {text: string; stat?: string; accent?: string; projectLogo?: string | null; bg?: string | null; brand: string; points?: string[]};
export const Thumb: React.FC<ThumbProps> = ({text, stat, accent: acIn = '#4F5BD5', projectLogo, bg, brand, points = []}) => {
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
        <div style={{position: 'absolute', left: 64, top: 150, width: points.length ? 740 : 820, display: 'flex', flexWrap: 'wrap', columnGap: 22,
          fontWeight: 800, fontSize: points.length ? 80 : words.join(' ').length > 28 ? 92 : 112, lineHeight: 1.02, color: C.ink, letterSpacing: -1}}>
          {words.map((w, i) => <span key={i} style={{color: i % 3 === 1 ? accent : C.ink}}>{w}</span>)}
        </div>
        {stat ? <div style={{position: 'absolute', left: 64, bottom: 60, padding: '10px 30px', borderRadius: 20, background: accent,
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
        <div style={{position: 'absolute', right: 40, bottom: 30, color: 'rgba(19,24,54,0.7)', fontWeight: 700, fontSize: 28}}>@Trong0322</div>
      </AbsoluteFill>
    </AccentCtx.Provider>
  );
};
