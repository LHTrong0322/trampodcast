import {LayoutProbe} from './probe';
import React from 'react';
import {AbsoluteFill, Audio, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {ShortThumb} from './ShortThumb';
import {AccentCtx, tone, Backdrop, C, Captions, Chip, clamp, CountUp, FONT, RevealWords, useFonts} from './ui';
import {DataPanel} from './data';
import {BeatPanel} from './beats';
import {DEFAULT_ACCENT, InsightProps, QuoteCard} from './Insight';

// Video dọc 9:16 (TikTok / Shorts / Reels): 1 insight, kiểu "dữ liệu thật"
// Vùng an toàn (review 1915): trên 220, dưới 420, phải 140 điểm ảnh bị giao diện app che, không đặt chữ ở đó
export const InsightShort: React.FC<InsightProps> = (props) => {
  useFonts();
  const {durationInFrames, width} = useVideoConfig();
  const f = useCurrentFrame();
  const sc = props.scenes[0];
  if (!sc) return null;
  const ac = sc.project?.color || DEFAULT_ACCENT;
  const hasData = !!(sc.data && sc.data.type && sc.data.type !== 'none');
  const cover = (props as any).cover;
  const cta = (props as any).cta as {text: string; from: number} | undefined;
  // Trọng 24/11 "tiêu đề bị thẻ đè": ước số dòng tiêu đề rồi đẩy thẻ xuống (và thu thẻ lại) cho khỏi chồng chữ
  const title = props.shortTitle || sc.heading || '';
  const tSize = title.length > 45 ? 50 : title.length > 30 ? 56 : 62;
  const tLines = Math.max(1, Math.ceil((title.length * tSize * 0.56) / 860));
  // review 27/11: nhãn dự án chỉ khi tiêu đề short nói về dự án đó (nhãn "Hyperliquid" trên tin ETF bị chê lặp, gây hiểu nhầm chủ đề)
  const nrm = (x: string) => x.toLowerCase().normalize('NFD').replace(/[^a-z0-9]/g, '');
  const chipTopic = !!sc.project?.name && [sc.project?.name, (sc.project as any)?.ticker].filter(Boolean)
    .some((x) => nrm(title).includes(nrm(String(x).split(/\s+/)[0])));
  const TOP = 270;   // review 27/11: header hạ thấp khỏi mép trên (trước 230)
  const titleBottom = TOP + 60 + 24 + (chipTopic ? 44 + 24 : 0) + tLines * tSize * 1.22;
  const cardTop = Math.max(560, Math.ceil(titleBottom + 40));
  // review 27/11: thẻ chỉ chiếm 1/3 màn, nửa dưới trống: thẻ cao hơn (600 thay 560), phụ đề hạ sát vùng an toàn
  const cardH = Math.max(480, 600 - Math.round((cardTop - 560) / 1.25));
  const srcLabel = (props as any).sourceLabel as string | undefined;
  // review 26/11 (short ETF 6.0): nhãn dự án chỉ hiện từ lúc lời đọc nhắc tới (không gắn "Hyperliquid" khi đang nói ETF)
  const norm = (x: string) => x.toLowerCase().normalize('NFD').replace(/[^a-z0-9]/g, '');
  const pKeys = [sc.project?.name, (sc.project as any)?.ticker].filter(Boolean).map((x) => norm(String(x).split(/\s+/)[0]));
  const hit = pKeys.length ? (sc.words || []).find((w) => pKeys.includes(norm(w.t))) : undefined;
  const chipOn = chipTopic && (!hit || f / 30 >= hit.s - 0.2);
  const ownSrc = !sc.source || /trong0322/i.test(sc.source);
  return (
    <AccentCtx.Provider value={tone(ac)}>
      <AbsoluteFill style={{background: C.bg}}>
        {props.audio ? <Audio src={staticFile(props.audio)} /> : null}
        <Backdrop />
        <div style={{position: 'absolute', top: TOP, left: 70, right: 150, display: 'flex', flexDirection: 'column', gap: 24}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            <Img src={staticFile('logo.png')} style={{width: 60, height: 60, borderRadius: 99}} />
            <div style={{fontFamily: FONT}}>
              <div style={{fontWeight: 800, color: C.ink, fontSize: 28, letterSpacing: 2}}>{(props.brand.name || '').toUpperCase()}</div>
              {/* review 24/11 + 26/11: nguồn tin không viết liền với tên kênh, chuyển xuống 1 dòng nhỏ riêng dưới thẻ */}
              <div style={{color: C.muted, fontWeight: 600, fontSize: 22}}>@Trong0322{!srcLabel && !ownSrc ? <> · Source: <span style={{color: C.ink}}>{sc.source}</span></> : null}</div>
            </div>
          </div>
          {chipTopic ? <div style={{display: 'flex', gap: 12, flexWrap: 'wrap', opacity: chipOn ? 1 : 0}}><Chip text={sc.project!.name} size={26} /></div> : null}
          <RevealWords text={title} size={tSize} delay={4} stagger={3} maxWidth={860}
            highlight={[sc.project?.name || ''].filter(Boolean)} />
        </div>
        {/* review 23/11: thẻ phóng 1,25 lần gần kín ngang màn, phụ đề hạ thấp (khoảng 1480 đến 1530) để không che thẻ, vẫn trên vùng nút TikTok */}
        <div style={{position: 'absolute', top: cardTop, left: 15, transform: 'scale(1.25)', transformOrigin: 'top left'}}>
          {sc.beats?.length ? <BeatPanel beats={sc.beats} t={f / 30} sceneDur={sc.dur} data={props.data} w={840} h={cardH} />
            : hasData ? <DataPanel spec={sc.data!} data={props.data} w={860} h={500} />
            : <QuoteCard post={props.post} quote={sc.quote || sc.heading || ''} w={860} h={500} />}
        </div>
        {sc.keyStat && !sc.beats?.length ? <div style={{position: 'absolute', top: 1215, left: 70, display: 'flex', alignItems: 'center', gap: 24}}>
          <CountUp value={sc.keyStat} size={72} delay={20} /><div style={{fontFamily: FONT, color: C.muted, fontSize: 30, fontWeight: 600, maxWidth: 480}}>{sc.keyLabel}</div>
        </div> : null}
        {/* review 26/11: nguồn tin không còn ở header, ghi nhỏ trong từng thẻ số liệu (source của beat) */}
        {/* review 26/11: phụ đề nâng lên khỏi vùng nút/tên kênh của TikTok, Shorts (trước bottom 390) */}
        <Captions words={sc.words} bottom={430} size={56} maxWidth={940} perChunk={5} />
        {cover && f < 40 ? <AbsoluteFill style={{opacity: interpolate(f, [26, 40], [1, 0], clamp)}}><ShortThumb {...cover} /></AbsoluteFill> : null}
        <div style={{position: 'absolute', left: 0, bottom: 0, height: 8, width: (f / durationInFrames) * width, background: ac}} />
        {cta && f >= cta.from * 30 ? <EndCard text={cta.text} t={f - cta.from * 30} /> : null}
        {(props as any).lint ? <LayoutProbe /> : null}
      </AbsoluteFill>
    </AccentCtx.Provider>
  );
};

// Trọng 22/11: khung kết mọi short, nền trắng sạch, chữ mời xem full video (nằm trong vùng an toàn 220..1500)
const EndCard: React.FC<{text: string; t: number}> = ({text, t}) => {
  const op = interpolate(t, [0, 3], [0, 1], clamp);   // review 27/11: hiện gọn trong 0,1 giây, không chồng chữ lên thẻ câu hỏi
  const up = interpolate(t, [0, 12], [40, 0], clamp);
  const pop = interpolate(t, [0, 10], [0.8, 1], clamp);
  return (
    <AbsoluteFill style={{background: '#FFFFFF', alignItems: 'center', justifyContent: 'center'}}>
      {/* review 27/11: nền trắng che hẳn thẻ cũ ngay khung đầu (trước đây mờ dần nên chữ chồng chữ), chỉ phần chữ hiện dần */}
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 40, marginTop: -160, padding: '0 80px', opacity: op}}>
        <Img src={staticFile('logo.png')} style={{width: 260, height: 260, borderRadius: 999, transform: `scale(${pop})`}} />
        <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 76, lineHeight: 1.15, color: C.ink, textAlign: 'center',
          textTransform: 'uppercase', transform: `translateY(${up}px)`}}>{text}</div>
        <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 34, color: C.muted, transform: `translateY(${up}px)`}}>YouTube: @smartpenguininsights</div>
      </div>
    </AbsoluteFill>
  );
};
