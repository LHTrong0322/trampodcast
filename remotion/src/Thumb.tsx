import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {AccentCtx, applyTheme, clean, BRAND, Handle, T, C, DISPLAY, FONT, HEAD, useFonts} from './ui';

// Ảnh bìa YouTube 1280×720: chữ to, 1 con số, logo dự án + logo kênh
export type ThumbProps = {text: string; stat?: string; accent?: string; projectLogo?: string | null; bg?: string | null; brand: string; theme?: string};
export const Thumb: React.FC<ThumbProps> = ({text, stat, accent: acc, projectLogo, bg, brand, theme}) => {
  applyTheme(theme);
  const accent = acc || BRAND.blue;
  useFonts();
  const words = clean(text || '').toUpperCase().split(/\s+/);
  return (
    <AccentCtx.Provider value={accent}>
      <AbsoluteFill style={{background: T.grad, fontFamily: FONT}}>
        {bg ? <Img src={staticFile(bg)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: 0.35, filter: 'saturate(0.8)'}} /> : null}
        <AbsoluteFill style={{background: `radial-gradient(900px 600px at 15% 20%, ${accent}40, transparent 70%), linear-gradient(90deg, ${C.bg} 35%, rgba(10,12,18,0.4))`}} />
        <div style={{position: 'absolute', left: 64, top: 48, display: 'flex', alignItems: 'center', gap: 14}}>
          <Img src={staticFile('logo.png')} style={{width: 64, height: 64, borderRadius: 99}} />
          <div style={{color: C.ink, fontFamily: HEAD, fontWeight: 700, fontSize: 26, letterSpacing: 2}}>{brand.toUpperCase()}</div>
        </div>
        <div style={{position: 'absolute', left: 64, top: 140, width: projectLogo ? 720 : 1100, height: stat ? 300 : 480, display: 'flex',
          flexWrap: 'wrap', alignContent: 'flex-start', columnGap: 20, overflow: 'hidden', fontFamily: DISPLAY,
          fontWeight: 800, fontSize: Math.max(58, Math.min(96, Math.round(2000 / Math.max(12, words.join(' ').length)))), lineHeight: 1.2,
          color: C.ink, letterSpacing: -1}}>
          {words.map((w, i) => <span key={i} style={{color: i % 3 === 1 ? accent : C.ink}}>{w}</span>)}
        </div>
        {stat ? <div style={{position: 'absolute', left: 64, bottom: 54, padding: '6px 34px', borderRadius: 24, background: BRAND.orange,
          color: C.bg, fontFamily: DISPLAY, fontWeight: 800, fontSize: 140, lineHeight: 1.15, transform: 'rotate(-3deg)',
          boxShadow: '0 20px 60px rgba(200,255,61,0.35)'}}>{stat}</div> : null}
        {projectLogo ? <Img src={staticFile(projectLogo)} style={{position: 'absolute', right: 110, top: 200, width: 300, height: 300, borderRadius: '50%',
          boxShadow: `0 0 0 10px ${accent}55, 0 30px 80px rgba(0,0,0,0.6)`}} /> : null}
        <Handle size={28} style={{position: 'absolute', right: 40, bottom: 30}} />
      </AbsoluteFill>
    </AccentCtx.Provider>
  );
};
