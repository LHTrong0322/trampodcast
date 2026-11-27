import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {AccentCtx, tone, FONT, useFonts} from './ui';
import {Sticker, ThumbIcon} from './Thumb';

// Ảnh bìa video ngắn 1080×1920 (Reels, Shorts, TikTok), cùng kiểu "viral sạch" với ảnh bìa YouTube (Trọng 26/11):
//   chữ viết thường có dấu như câu nói, 1 con số khổng lồ làm nhân vật chính, thẻ trắng bo góc, nhãn vàng, avatar penguin khi không có số.
// Vùng an toàn: chữ chính nằm giữa màn để giao diện app không che (trên 230px, dưới 440px).
// Nhãn kênh: YouTube là @smartpenguininsights, @Trong0322 là X (Trọng 26/11).
// Ảnh này cũng là khung hình đầu của short (InsightShort), nên giữ gọn, đọc được khi thu nhỏ trong lưới video.
export type ShortThumbProps = {text: string; stat?: string; label?: string; points?: string[]; accent?: string;
  projectLogo?: string | null; brand: string; icon?: ThumbIcon; news?: boolean; tag?: string; tagline?: string; vs?: {label: string; value: string; tone?: string; logo?: string | null}[]};

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

export const ShortThumb: React.FC<ShortThumbProps> = ({text, stat = '', label = '', points = [], accent: acIn = '#4F5BD5', projectLogo, brand, vs = [], news = false, tag = '', tagline = '', icon = 'none'}) => {
  // Trọng 27/11: short bài học (chuỗi Phân tích kỹ thuật từ số 0) không gắn nhãn "Tin nóng"
  // Trọng 26/11 (ghi nhớ bằng code): nhắc dự án thì có logo, chủ đề khớp hình dán thì có hình dán.
  const stk = icon && icon !== 'none' ? icon : null;
  const accent = tone(acIn);
  useFonts();
  const t = (text || '').replace(/_/g, ' ');
  const len = t.length;
  // Trọng 24/11 + 26/11: không tách cụm (vd "S&P / 500", "225 / tỷ đô") và không để 1 từ mồ côi ở dòng cuối.
  // Dấu _ trong kịch bản dính các chữ thành 1 cụm; tự dính thêm: "S&P 500", số + đơn vị, 2 từ cuối khi từ cuối ngắn.
  // Lưu ý: \s trong JS khớp cả dấu cách không ngắt ( ), nên chỉ tách theo dấu cách thường.
  const UNIT = /^(tỷ|triệu|nghìn|ngàn|năm|ngày|tháng|tuần|phiên|lần|câu|bước|điều|coin|đô|USD|%)[?!.,:]?$/i;
  const glued: string[] = [];
  (text || '').split(/[ \t\n]+/).filter(Boolean).forEach((w) => {
    const prev = glued[glued.length - 1];
    if (prev !== undefined && (/S&P$/i.test(prev) || (/\d/.test(prev) && UNIT.test(w)))) glued[glued.length - 1] = `${prev} ${w}`;
    else glued.push(w);
  });
  if (glued.length > 2 && glued[glued.length - 1].replace(/[?!.,]/g, '').length <= 5) glued.splice(-2, 2, `${glued[glued.length - 2]} ${glued[glued.length - 1]}`);
  const size = len > 46 ? 84 : len > 32 ? 96 : len > 20 ? 110 : 124;
  // số trong tiêu đề tô màu (giảm đỏ, tăng xanh) như bản cũ, chữ còn lại màu mực
  const words = glued.map((w) => w.replace(/[_ ]/g, '\u00A0'));
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
          {news || tag ? <span style={{marginLeft: 8, background: tag ? '#4F5BD5' : RED, color: '#FFFFFF', borderRadius: 14, padding: '6px 18px', fontSize: 30, fontWeight: 800}}>{tag || 'Tin nóng'}</span> : null}
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
            {projectLogo ? <Img src={staticFile(projectLogo)} style={{position: 'absolute', right: -24, top: -60, width: 150, height: 150, borderRadius: 99,
              border: '8px solid #FFFFFF', background: '#FFFFFF', boxShadow: '0 14px 36px rgba(20,24,51,0.2)'}} />
              : stk ? <div style={{position: 'absolute', right: -24, top: -70}}><Sticker kind={stk} size={160} color={accent} rotate={10} /></div> : null}
            <div style={{fontSize: fit(stat, projectLogo || stk ? 700 : 820, 280, /%|tháng|năm/.test(stat) ? 0.7 : 0.62), lineHeight: 1, letterSpacing: '-0.05em', whiteSpace: 'nowrap', color: valueColor(stat) === INK ? accent : valueColor(stat)}}>{stat}</div>
            {label ? <div style={{marginTop: 20, fontSize: fit(label, 840, 46, 0.55), fontWeight: 700, color: MUTED, lineHeight: 1.2}}>{label}</div> : null}
          </div>
        ) : points.length ? null : (
          <div style={{position: 'absolute', left: 0, right: 0, top: Math.min(Math.max(below, 780), 900), display: 'flex', justifyContent: 'center'}}>
            <div style={{width: 400, height: 400, borderRadius: '50%', overflow: 'hidden', border: '14px solid #FFFFFF', background: projectLogo ? '#FFFFFF' : '#A9CBF2',
              boxShadow: '0 24px 60px rgba(20,24,51,0.18)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
              <Img src={staticFile(projectLogo || 'logo.png')} style={projectLogo ? {width: '78%', height: '78%', objectFit: 'contain'} : {width: '100%', height: '100%'}} />
            </div>
            {stk ? <div style={{position: 'absolute', left: 620, top: 250}}><Sticker kind={stk} size={180} color={accent} rotate={10} /></div> : null}
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

        <div style={{position: 'absolute', left: 70, bottom: 460, display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 14}}>
          <span style={{background: YEL, borderRadius: 20, padding: '12px 30px', fontSize: 42, boxShadow: '0 12px 30px rgba(20,24,51,0.12)'}}>
            {tagline || (news ? 'Tin nóng hôm nay' : 'Xem full trên YouTube')}</span>
          <span style={{fontSize: 34, fontWeight: 700, color: MUTED}}>@smartpenguininsights</span>
        </div>
      </AbsoluteFill>
    </AccentCtx.Provider>
  );
};
