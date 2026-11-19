import React from 'react';
import {AbsoluteFill, Audio, Img, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {AccentCtx, applyTheme, deepClean, tone, Backdrop, BRAND, Handle, C, Captions, Chip, CountUp, FONT, HEAD, RevealWords, useFonts} from './ui';
import {DataPanel} from './data';
import {accentDefault, InsightProps, QuoteCard} from './Insight';

// Video dọc 9:16 (TikTok / Shorts / Reels): 1 insight, kiểu "dữ liệu thật"
export const InsightShort: React.FC<InsightProps> = (raw) => {
  const props = React.useMemo(() => deepClean(raw), [raw]);
  applyTheme(props.theme);
  useFonts();
  const {durationInFrames, width} = useVideoConfig();
  const f = useCurrentFrame();
  const sc = props.scenes[0];
  if (!sc) return null;
  const ac = tone(sc.project?.color) || accentDefault();
  const hasData = !!(sc.data && sc.data.type && sc.data.type !== 'none');
  return (
    <AccentCtx.Provider value={ac}>
      <AbsoluteFill style={{background: C.bg}}>
        {props.audio ? <Audio src={staticFile(props.audio)} /> : null}
        <Backdrop />
        <div style={{position: 'absolute', top: 110, left: 70, right: 70, display: 'flex', flexDirection: 'column', gap: 28}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            <Img src={staticFile('logo.png')} style={{width: 60, height: 60, borderRadius: 99}} />
            <div style={{fontFamily: FONT}}>
              <div style={{fontFamily: HEAD, fontWeight: 700, color: C.ink, fontSize: 28, letterSpacing: 2}}>{(props.brand.name || '').toUpperCase()}</div>
              {sc.source ? <div style={{color: C.muted, fontWeight: 600, fontSize: 22}}>Source: <span style={{color: C.ink}}>{sc.source}</span></div> : null}
            </div>
          </div>
          {sc.project?.name ? <div><Chip text={sc.project.name} size={28} /></div> : null}
          <RevealWords text={props.shortTitle || sc.heading || ''} size={(props.shortTitle || sc.heading || '').length > 45 ? 56 : 64} delay={4} stagger={3} maxWidth={940}
            highlight={[sc.project?.name || ''].filter(Boolean)} />
        </div>
        <div style={{position: 'absolute', top: 620, left: 70}}>
          {hasData ? <DataPanel spec={sc.data!} data={props.data} w={940} h={580} />
            : <QuoteCard post={props.post} quote={sc.quote || sc.heading || ''} w={940} h={580} emph={sc.emph} />}
        </div>
        {sc.keyStat ? <div style={{position: 'absolute', top: 1250, left: 70, display: 'flex', alignItems: 'center', gap: 24}}>
          <CountUp value={sc.keyStat} size={76} delay={20} color={BRAND.orange} /><div style={{fontFamily: FONT, color: C.muted, fontSize: 30, fontWeight: 600, maxWidth: 480}}>{sc.keyLabel}</div>
        </div> : null}
        <Captions words={sc.words} bottom={300} size={50} maxWidth={960} perChunk={8} emph={sc.emph} />
        <div style={{position: 'absolute', bottom: 120, left: 0, right: 0, display: 'flex', justifyContent: 'center'}}>
          <Chip text="Xem full trên YouTube · Smart Penguin Insights" color={C.red} size={26} />
        </div>
        <div style={{position: 'absolute', left: 0, bottom: 0, height: 8, width: (f / durationInFrames) * width, background: ac}} />
        <Handle size={24} style={{position: 'absolute', right: 40, top: 40}} />
      </AbsoluteFill>
    </AccentCtx.Provider>
  );
};
