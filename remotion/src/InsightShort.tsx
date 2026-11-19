import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Backdrop, C, Captions, Chip, CountUp, FONT, Glitch, ImageDeck, RevealWords, useFonts} from './ui';
import {DataPanel} from './data';
import type {InsightProps} from './Insight';

// Video dọc 9:16: 1 insight, chữ to, phụ đề kiểu TikTok ở giữa dưới
export const InsightShort: React.FC<InsightProps> = (props) => {
  useFonts();
  const {fps, durationInFrames, width} = useVideoConfig();
  const f = useCurrentFrame();
  const sc = props.scenes[0];
  if (!sc) return null;
  const hasData = !!(sc.data && sc.data.type && sc.data.type !== 'none');
  const dataAt = sc.dur * 0.5;
  return (
    <AbsoluteFill style={{background: C.bg}}>
      {props.audio ? <Audio src={staticFile(props.audio)} /> : null}
      {props.music ? <Audio src={staticFile(props.music)} volume={0.12} /> : null}
      <Backdrop img={props.mode === 'data' ? undefined : sc.images?.[0]} dim={0.82} />
      <div style={{position: 'absolute', top: 120, left: 70, right: 70, display: 'flex', flexDirection: 'column', gap: 30}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
          <Img src={staticFile('logo.png')} style={{width: 64, height: 64, borderRadius: 99, border: `2px solid ${C.violet}`}} />
          <div style={{fontFamily: FONT, fontWeight: 800, color: C.ink, fontSize: 30, letterSpacing: 2}}>{(props.brand.name || '').toUpperCase()}</div>
        </div>
        <RevealWords text={sc.hook || sc.heading || ''} size={78} delay={4} stagger={3} maxWidth={940} />
      </div>
      <div style={{position: 'absolute', top: 640, left: 70}}>
        {props.mode === 'data' && hasData ? <DataPanel spec={sc.data!} data={props.data} w={940} h={620} />
          : f / fps < dataAt || !hasData ? <ImageDeck images={sc.images || []} dur={hasData ? dataAt : sc.dur} w={940} h={620} tilt={0} />
            : <Sequence from={Math.round(dataAt * fps)} layout="none"><DataPanel spec={sc.data!} data={props.data} w={940} h={620} /></Sequence>}
      </div>
      {sc.keyStat ? <div style={{position: 'absolute', top: 1200, left: 70, display: 'flex', alignItems: 'center', gap: 24}}>
        <CountUp value={sc.keyStat} size={96} delay={20} /><div style={{fontFamily: FONT, color: C.muted, fontSize: 30, fontWeight: 600, maxWidth: 440}}>{sc.keyLabel}</div>
      </div> : null}
      <Captions words={sc.words} bottom={300} size={58} maxWidth={960} perChunk={4} />
      <div style={{position: 'absolute', bottom: 150, left: 0, right: 0, display: 'flex', justifyContent: 'center'}}>
        <Chip text="Xem full trên YouTube · @Trong0322" color={C.red} size={28} />
      </div>
      <div style={{position: 'absolute', left: 0, bottom: 0, height: 10, width: (f / durationInFrames) * width, background: C.cyan}} />
      <Glitch />
    </AbsoluteFill>
  );
};
