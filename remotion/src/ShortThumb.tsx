import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {AccentCtx, tone, C, FONT, useFonts} from './ui';

// Ảnh bìa video ngắn 1080×1920 (Reels, Shorts, TikTok). Chữ chính nằm giữa màn để không bị
// giao diện app che (trên 230px, dưới 440px), đọc được khi thu nhỏ trong lưới video của trang.
export type ShortThumbProps = {text: string; stat?: string; label?: string; points?: string[]; accent?: string;
  projectLogo?: string | null; brand: string};
export const ShortThumb: React.FC<ShortThumbProps> = ({text, stat, label, points = [], accent: acIn = '#4F5BD5', projectLogo, brand}) => {
  const accent = tone(acIn);
  useFonts();
  const words = (text || '').toUpperCase().split(/\s+/).filter(Boolean);
  const long = words.join(' ').length;
  const size = long > 44 ? 92 : long > 26 ? 104 : 120;   // Trọng 22/11: nhỏ lại cho khỏi mất dấu
  return (
    <AccentCtx.Provider value={accent}>
      <AbsoluteFill style={{background: C.bg, fontFamily: FONT}}>
        <AbsoluteFill style={{background: `radial-gradient(900px 900px at 20% 30%, ${accent}38, transparent 70%),
          radial-gradient(700px 700px at 90% 85%, ${accent}22, transparent 70%)`}} />
        <div style={{position: 'absolute', left: 70, top: 250, display: 'flex', alignItems: 'center', gap: 18}}>
          <Img src={staticFile('logo.png')} style={{width: 84, height: 84, borderRadius: 99}} />
          <div style={{color: C.ink, fontWeight: 800, fontSize: 34, letterSpacing: 2}}>{brand.toUpperCase()}</div>
        </div>
        <div style={{position: 'absolute', left: 70, right: 70, top: 420, display: 'flex', flexWrap: 'wrap', columnGap: 26,
          fontWeight: 800, fontSize: size, lineHeight: 1.32, color: C.ink, letterSpacing: 0}}>
          {words.map((w, i) => <span key={i} style={{color: i % 3 === 1 ? accent : C.ink}}>{w}</span>)}
        </div>
        {stat ? (
          <div style={{position: 'absolute', left: 70, top: 1070, display: 'flex', alignItems: 'center', gap: 26}}>
            <div style={{padding: '14px 36px', borderRadius: 26, background: accent, color: '#FFFFFF', fontWeight: 800, fontSize: 110, lineHeight: 1.05}}>{stat}</div>
            {label ? <div style={{color: C.muted, fontWeight: 700, fontSize: 38, maxWidth: 480, lineHeight: 1.15}}>{label}</div> : null}
          </div>
        ) : null}
        {points.length ? (
          <div style={{position: 'absolute', left: 70, right: 70, top: stat ? 1250 : 1100, display: 'flex', flexDirection: 'column', gap: 22}}>
            {points.slice(0, 3).map((p, i) => (
              <div key={i} style={{display: 'flex', alignItems: 'center', gap: 20, background: '#FFFFFF', borderRadius: 22,
                padding: '18px 24px', border: `1px solid ${C.line}`, boxShadow: '0 12px 34px rgba(40,50,110,0.10)'}}>
                <div style={{width: 54, height: 54, borderRadius: 14, background: accent, color: '#FFFFFF', fontSize: 34, fontWeight: 800,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>{i + 1}</div>
                <div style={{color: C.ink, fontWeight: 700, fontSize: 40, lineHeight: 1.15}}>{p}</div>
              </div>
            ))}
          </div>
        ) : null}
        {projectLogo ? <Img src={staticFile(projectLogo)} style={{position: 'absolute', right: 80, top: 230, width: 150, height: 150,
          borderRadius: '50%', boxShadow: `0 0 0 8px ${accent}44`}} /> : null}
        <div style={{position: 'absolute', left: 70, bottom: 470, display: 'flex', alignItems: 'center', gap: 14, color: 'rgba(19,24,54,0.75)',
          fontWeight: 700, fontSize: 36}}>Xem bản đầy đủ trên YouTube · @Trong0322</div>
      </AbsoluteFill>
    </AccentCtx.Provider>
  );
};
