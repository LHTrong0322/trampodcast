import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {AccentCtx, tone, FONT, useFonts} from './ui';
import {ThumbIcon} from './Thumb';

// Ảnh bìa video ngắn 1080×1920 (Reels, Shorts, TikTok), cùng kiểu "viral sạch" với ảnh bìa YouTube (Trọng 26/11):
//   chữ viết thường có dấu như câu nói, 1 con số khổng lồ làm nhân vật chính, thẻ trắng bo góc, nhãn vàng, avatar penguin khi không có số.
// Vùng an toàn: chữ chính nằm giữa màn để giao diện app không che (trên 230px, dưới 440px).
// Ảnh này cũng là khung hình đầu của short (InsightShort), nên giữ gọn, đọc được khi thu nhỏ trong lưới video.
export type ShortThumbProps = {text: string; stat?: string; label?: string; points?: string[]; accent?: string;
  projectLogo?: string | null; brand: string; icon?: ThumbIcon; news?: boolean; vs?: {label: string; value: string; tone?: string; logo?: string | null}[]};

const RED = '#E5383B', GREEN = '#1F9D63', YEL = '#FFD84D', INK = '#141833', MUTED = '#5A6080';
const valueColor = (v: string) => (/^\s*[-−]/.test(v) ? RED : /^\s*\+/.test(v) ? GREEN : INK);
// số trong tiêu đề: có dấu thì theo dấu; đứng sau "giảm, mất, bốc hơi, lỗ, sập" thì đỏ, sau "tăng, lãi, x" thì xanh, còn lại màu nhấn
const numColor = (w: string, prev: string, accent: string) => {
  if (!/\d/.test(w)) return INK;
  if (valueColor(w) !== INK) return valueColor(w);
  if (/giảm|mất|bốc hơi|lỗ|sập|rơi|bán tháo|thua/i.test(prev)) return RED;
  if (/tăng|lãi|thắng|gấp/i.test(prev)) return GREEN;
  return accent;
};
const fit = (t: string, maxW: number, maxSize: number, em = 0.6) => Math.round(Math.min(maxSize, maxW / Math.max(1, (t || '').length * em)));
const card: React.CSSProperties = {background: '#FFFFFF', borderRadius: 36, boxShadow: '0 24px 60px rgba(20,24,51,0.12), 0 2px 6px rgba(20,24,51,0.05)'};

export const ShortThumb: React.FC<ShortThumbProps> = ({text, stat = '', label = '', points = [], accent: acIn = '#4F5BD5', projectLogo, brand, vs = [], news = false}) => {
  const accent = tone(acIn);
  useFonts();
  const t = (text || '').replace(/_/g, ' ');
  const len = t.length;
  const size = len > 46 ? 84 : len > 32 ? 96 : len > 20 ? 110 : 124;
  // số trong tiêu đề tô màu (giảm đỏ, tăng xanh) như bản cũ, chữ còn lại màu mực
  const words = t.split(/\s+/).filter(Boolean);
  const hasVs = vs.length >= 2;
  const top = 400;
  const titleH = Math.ceil((len * size * 0.58) / 940) * size * 1.22;   // ước lượng chiều cao tiêu đề để xếp khối bên dưới
  const below = top + titleH + 60;
  return (
    <AccentCtx.Provider value={accent}>
      <AbsoluteFill style={{fontFamily: FONT, fontWeight: 800, color: INK, overflow: 'hidden',
        background: `radial-gradient(ellipse 70% 50% at 80% 55%, ${accent}24, transparent 70%), #F6F7FC`}}>
        <AbsoluteFill style={{backgroundImage: 'linear-gradient(rgba(79,91,213,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(79,91,213,0.06) 1px, transparent 1px)',
          backgroundSize: '72px 72px'}} />
        <div style={{position: 'absolute', left: 70, top: 250, display: 'flex', alignItems: 'center', gap: 16, fontSize: 32, fontWeight: 700, color: MUTED}}>
          <Img src={staticFile('logo.png')} style={{width: 72, height: 72, borderRadius: 99, border: '4px solid #FFFFFF', boxShadow: '0 6px 16px rgba(20,24,51,0.15)'}} />
          {brand}
          {news ? <span style={{marginLeft: 8, background: RED, color: '#FFFFFF', borderRadius: 14, padding: '6px 18px', fontSize: 30, fontWeight: 800}}>Tin nóng</span> : null}
        </div>
        <div style={{position: 'absolute', left: 70, right: 70, top, fontSize: size, lineHeight: 1.18, letterSpacing: '-0.02em',
          display: 'flex', flexWrap: 'wrap', columnGap: size * 0.26}}>
          {words.map((w, i) => <span key={i} style={{color: numColor(w, words.slice(Math.max(0, i - 3), i).join(' '), accent)}}>{w}</span>)}
        </div>

        {hasVs ? (
          <div style={{position: 'absolute', left: 70, right: 70, top: Math.min(Math.max(below, 860), 1010), display: 'flex', flexDirection: 'column', gap: 28}}>
            {vs.slice(0, 2).map((x, i) => (
              <div key={i} style={{...card, display: 'flex', alignItems: 'center', gap: 24, padding: '24px 34px'}}>
                {x.logo ? <Img src={staticFile(x.logo)} style={{width: 104, height: 104, borderRadius: 99, flexShrink: 0, boxShadow: '0 12px 30px rgba(20,24,51,0.16)'}} /> : null}
                <div style={{fontSize: 52, color: MUTED, fontWeight: 700}}>{x.label}</div>
                <div style={{flex: 1}} />
                <div style={{fontSize: fit(x.value, 420, 120), letterSpacing: '-0.04em', whiteSpace: 'nowrap',
                  color: x.tone === 'down' ? RED : x.tone === 'up' ? GREEN : valueColor(x.value)}}>{x.value}</div>
              </div>
            ))}
            <div style={{position: 'absolute', left: '50%', top: '50%', width: 110, height: 110, marginLeft: -55, marginTop: -55, borderRadius: 99, background: YEL,
              fontSize: 42, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 12px 30px rgba(20,24,51,0.18)'}}>VS</div>
          </div>
        ) : stat ? (
          <div style={{position: 'absolute', left: 70, right: 70, top: Math.max(below, 820), ...card, padding: '44px 50px 48px', textAlign: 'left'}}>
            <div style={{fontSize: fit(stat, 840, 280, 0.6), lineHeight: 1, letterSpacing: '-0.05em', whiteSpace: 'nowrap', color: valueColor(stat) === INK ? accent : valueColor(stat)}}>{stat}</div>
            {label ? <div style={{marginTop: 20, fontSize: fit(label, 840, 46, 0.55), fontWeight: 700, color: MUTED, lineHeight: 1.2}}>{label}</div> : null}
          </div>
        ) : points.length ? null : (
          <div style={{position: 'absolute', left: 0, right: 0, top: Math.min(Math.max(below, 780), 900), display: 'flex', justifyContent: 'center'}}>
            <div style={{width: 400, height: 400, borderRadius: '50%', overflow: 'hidden', border: '14px solid #FFFFFF', background: projectLogo ? '#FFFFFF' : '#A9CBF2',
              boxShadow: '0 24px 60px rgba(20,24,51,0.18)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
              <Img src={staticFile(projectLogo || 'logo.png')} style={projectLogo ? {width: '78%', height: '78%', objectFit: 'contain'} : {width: '100%', height: '100%'}} />
            </div>
          </div>
        )}

        {points.length && !hasVs && !stat ? (   // có số thì bỏ danh sách: ít chữ, số là nhân vật chính

          <div style={{position: 'absolute', left: 70, right: 70, top: Math.max(below, 880), display: 'flex', flexDirection: 'column', gap: 22}}>
            {points.slice(0, 3).map((p, i) => (
              <div key={i} style={{...card, borderRadius: 26, display: 'flex', alignItems: 'center', gap: 22, padding: '20px 28px'}}>
                <div style={{width: 58, height: 58, borderRadius: 99, background: YEL, fontSize: 34, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>{i + 1}</div>
                <div style={{fontSize: 42, fontWeight: 700, lineHeight: 1.15}}>{p}</div>
              </div>
            ))}
          </div>
        ) : null}

        <div style={{position: 'absolute', left: 70, bottom: 460, display: 'flex', alignItems: 'center', gap: 20}}>
          <span style={{background: YEL, borderRadius: 20, padding: '12px 30px', fontSize: 42, boxShadow: '0 12px 30px rgba(20,24,51,0.12)'}}>
            {news ? 'Tin nóng hôm nay' : 'Xem full trên YouTube'}</span>
          <span style={{fontSize: 34, fontWeight: 700, color: MUTED}}>@Trong0322</span>
        </div>
      </AbsoluteFill>
    </AccentCtx.Provider>
  );
};
