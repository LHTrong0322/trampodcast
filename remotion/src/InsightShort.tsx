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
  return (
    <AccentCtx.Provider value={tone(ac)}>
      <AbsoluteFill style={{background: C.bg}}>
        {props.audio ? <Audio src={staticFile(props.audio)} /> : null}
        <Backdrop />
        <div style={{position: 'absolute', top: 230, left: 70, right: 150, display: 'flex', flexDirection: 'column', gap: 24}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            <Img src={staticFile('logo.png')} style={{width: 60, height: 60, borderRadius: 99}} />
            <div style={{fontFamily: FONT}}>
              <div style={{fontWeight: 800, color: C.ink, fontSize: 28, letterSpacing: 2}}>{(props.brand.name || '').toUpperCase()}</div>
              <div style={{color: C.muted, fontWeight: 600, fontSize: 22}}>@Trong0322{sc.source ? <> · Source: <span style={{color: C.ink}}>{sc.source}</span></> : null}</div>
            </div>
          </div>
          <div style={{display: 'flex', gap: 12, flexWrap: 'wrap'}}>{sc.project?.name ? <Chip text={sc.project.name} size={26} /> : null}</div>
          <RevealWords text={props.shortTitle || sc.heading || ''} size={(props.shortTitle || sc.heading || '').length > 45 ? 54 : 62} delay={4} stagger={3} maxWidth={860}
            highlight={[sc.project?.name || ''].filter(Boolean)} />
        </div>
        <div style={{position: 'absolute', top: 600, left: 60}}>
          {sc.beats?.length ? <BeatPanel beats={sc.beats} t={f / 30} sceneDur={sc.dur} data={props.data} w={960} h={700} />
            : hasData ? <DataPanel spec={sc.data!} data={props.data} w={860} h={500} />
            : <QuoteCard post={props.post} quote={sc.quote || sc.heading || ''} w={860} h={500} />}
        </div>
        {sc.keyStat && !sc.beats?.length ? <div style={{position: 'absolute', top: 1215, left: 70, display: 'flex', alignItems: 'center', gap: 24}}>
          <CountUp value={sc.keyStat} size={72} delay={20} /><div style={{fontFamily: FONT, color: C.muted, fontSize: 30, fontWeight: 600, maxWidth: 480}}>{sc.keyLabel}</div>
        </div> : null}
        <Captions words={sc.words} bottom={470} size={54} maxWidth={940} perChunk={5} />
        {cover && f < 40 ? <AbsoluteFill style={{opacity: interpolate(f, [26, 40], [1, 0], clamp)}}><ShortThumb {...cover} /></AbsoluteFill> : null}
        <div style={{position: 'absolute', left: 0, bottom: 0, height: 8, width: (f / durationInFrames) * width, background: ac}} />
        {cta && f >= cta.from * 30 ? <EndCard text={cta.text} t={f - cta.from * 30} /> : null}
      </AbsoluteFill>
    </AccentCtx.Provider>
  );
};

// Trọng 22/11: khung kết mọi short, nền trắng sạch, chữ mời xem full video (nằm trong vùng an toàn 220..1500)
const EndCard: React.FC<{text: string; t: number}> = ({text, t}) => {
  const op = interpolate(t, [0, 8], [0, 1], clamp);
  const up = interpolate(t, [0, 12], [40, 0], clamp);
  const pop = interpolate(t, [0, 10], [0.8, 1], clamp);
  return (
    <AbsoluteFill style={{background: '#FFFFFF', opacity: op, alignItems: 'center', justifyContent: 'center'}}>
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 40, marginTop: -160, padding: '0 80px'}}>
        <Img src={staticFile('logo.png')} style={{width: 260, height: 260, borderRadius: 999, transform: `scale(${pop})`}} />
        <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 76, lineHeight: 1.15, color: C.ink, textAlign: 'center',
          textTransform: 'uppercase', transform: `translateY(${up}px)`}}>{text}</div>
        <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 34, color: C.muted, transform: `translateY(${up}px)`}}>@Trong0322</div>
      </div>
    </AbsoluteFill>
  );
};
