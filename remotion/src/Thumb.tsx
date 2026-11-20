import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {AccentCtx, applyTheme, clean, fitSize, BRAND, Handle, T, C, DISPLAY, FONT, HEAD, useFonts} from './ui';

// Ảnh bìa YouTube 1280×720: hứa GIÁ TRỊ hành động được (vd "3 TIÊU CHÍ CHỌN ALTCOIN"), chữ to, 1 con số,
// bên phải là logo dự án hoặc thẻ checklist (không để khoảng trống thừa).
export type ThumbProps = {text: string; stat?: string; accent?: string; projectLogo?: string | null; bg?: string | null; brand: string;
  theme?: string; points?: string[]};
export const Thumb: React.FC<ThumbProps> = ({text, stat, accent: acc, projectLogo, bg, brand, theme, points}) => {
  applyTheme(theme);
  const accent = acc || BRAND.blue;
  useFonts();
  const words = clean(text || '').toUpperCase().split(/\s+/).filter(Boolean);
  const pts = (points || []).map((p) => clean(p)).filter(Boolean).slice(0, 3);
  const right = projectLogo || pts.length;
  const W = right ? 700 : 1150;
  const H = stat ? 330 : 470;
  const size = fitSize(words.join(' '), W, H, 120, 56, 1.12, 0.74);
  return (
    <AccentCtx.Provider value={accent}>
      <AbsoluteFill style={{background: T.grad, fontFamily: FONT}}>
        {bg ? <Img src={staticFile(bg)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: 0.35, filter: 'saturate(0.8)'}} /> : null}
        <AbsoluteFill style={{background: `radial-gradient(900px 600px at 15% 20%, ${accent}30, transparent 70%)`}} />
        <div style={{position: 'absolute', left: 60, top: 40, display: 'flex', alignItems: 'center', gap: 14}}>
          <Img src={staticFile('logo.png')} style={{width: 60, height: 60, borderRadius: 99}} />
          <div style={{color: C.ink, fontFamily: HEAD, fontWeight: 700, fontSize: 24, letterSpacing: 2}}>{brand.toUpperCase()}</div>
        </div>
        <div style={{position: 'absolute', left: 60, top: 128, width: W, height: H, display: 'flex', flexWrap: 'wrap', alignContent: 'center',
          columnGap: size * 0.22, fontFamily: DISPLAY, fontWeight: 800, fontSize: size, lineHeight: 1.12, color: C.ink, letterSpacing: -1}}>
          {words.map((w, i) => <span key={i} style={{color: /\d/.test(w) || i % 3 === 1 ? accent : C.ink}}>{w}</span>)}
        </div>
        {stat ? <div style={{position: 'absolute', left: 60, bottom: 50, padding: '4px 30px', borderRadius: 22, background: accent,
          color: '#fff', fontFamily: DISPLAY, fontWeight: 800, fontSize: 120, lineHeight: 1.15, transform: 'rotate(-3deg)',
          boxShadow: `0 20px 50px ${accent}55`}}>{stat}</div> : null}
        {projectLogo ? <Img src={staticFile(projectLogo)} style={{position: 'absolute', right: 90, top: 170, width: 340, height: 340, borderRadius: '50%',
          boxShadow: `0 0 0 12px ${accent}44, 0 30px 80px rgba(0,0,0,0.35)`}} />
          : pts.length ? (
            <div style={{position: 'absolute', right: 50, top: 120, width: 450, padding: '30px 30px', borderRadius: 30, background: C.panel,
              border: `2px solid ${accent}55`, boxShadow: T.shadow, display: 'flex', flexDirection: 'column', gap: 24}}>
              {pts.map((p, i) => (
                <div key={i} style={{display: 'flex', alignItems: 'center', gap: 18}}>
                  <div style={{width: 64, height: 64, borderRadius: 16, background: accent, color: '#fff', fontSize: 44, fontWeight: 800,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>✓</div>
                  <div style={{color: C.ink, fontFamily: HEAD, fontWeight: 700, fontSize: fitSize(p, 320, 100, 44, 28), lineHeight: 1.1}}>{p}</div>
                </div>
              ))}
            </div>
          ) : null}
        <Handle size={28} style={{position: 'absolute', right: 40, bottom: 28}} />
      </AbsoluteFill>
    </AccentCtx.Provider>
  );
};
