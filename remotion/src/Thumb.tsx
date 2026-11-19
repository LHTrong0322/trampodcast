import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {AccentCtx, C, FONT, useFonts} from './ui';

// Ảnh bìa YouTube 1280×720: chữ to, 1 con số, logo dự án + logo kênh
export type ThumbProps = {text: string; stat?: string; accent?: string; projectLogo?: string | null; bg?: string | null; brand: string};
export const Thumb: React.FC<ThumbProps> = ({text, stat, accent = '#7C6CFF', projectLogo, bg, brand}) => {
  useFonts();
  const words = (text || '').toUpperCase().split(/\s+/);
  return (
    <AccentCtx.Provider value={accent}>
      <AbsoluteFill style={{background: C.bg, fontFamily: FONT}}>
        {bg ? <Img src={staticFile(bg)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: 0.35, filter: 'saturate(0.8)'}} /> : null}
        <AbsoluteFill style={{background: `radial-gradient(900px 600px at 15% 20%, ${accent}40, transparent 70%), linear-gradient(90deg, ${C.bg} 35%, rgba(10,12,18,0.4))`}} />
        <div style={{position: 'absolute', left: 64, top: 48, display: 'flex', alignItems: 'center', gap: 14}}>
          <Img src={staticFile('logo.png')} style={{width: 64, height: 64, borderRadius: 99}} />
          <div style={{color: C.ink, fontWeight: 800, fontSize: 26, letterSpacing: 2}}>{brand.toUpperCase()}</div>
        </div>
        <div style={{position: 'absolute', left: 64, top: 150, width: 820, display: 'flex', flexWrap: 'wrap', columnGap: 22,
          fontWeight: 800, fontSize: words.join(' ').length > 28 ? 92 : 112, lineHeight: 1.02, color: C.ink, letterSpacing: -1}}>
          {words.map((w, i) => <span key={i} style={{color: i % 3 === 1 ? accent : C.ink}}>{w}</span>)}
        </div>
        {stat ? <div style={{position: 'absolute', left: 64, bottom: 60, padding: '10px 30px', borderRadius: 20, background: accent,
          color: '#0A0C12', fontWeight: 800, fontSize: 92, lineHeight: 1.1}}>{stat}</div> : null}
        {projectLogo ? <Img src={staticFile(projectLogo)} style={{position: 'absolute', right: 110, top: 200, width: 300, height: 300, borderRadius: 99,
          boxShadow: `0 0 0 10px ${accent}55, 0 30px 80px rgba(0,0,0,0.6)`}} /> : null}
        <div style={{position: 'absolute', right: 40, bottom: 30, color: 'rgba(255,255,255,0.7)', fontWeight: 700, fontSize: 28}}>@Trong0322</div>
      </AbsoluteFill>
    </AccentCtx.Provider>
  );
};
