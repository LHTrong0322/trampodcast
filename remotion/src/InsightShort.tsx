import React from 'react';
import {AbsoluteFill, Audio, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {AccentCtx, applyTheme, clamp, deepClean, fitSize, tone, Backdrop, Handle, C, Captions, Chip, FONT, HEAD, useFonts} from './ui';
import {accentDefault, BeatStage, InsightProps, StatText} from './Insight';

// Video dọc 9:16 (TikTok / Shorts / Reels): 1 insight.
// Vùng an toàn: phụ đề đặt cao hơn vùng nút/mô tả của TikTok/Shorts (đáy ≥ 420px tính từ dưới) và tránh cột nút bên phải (~140px).
const SAFE_BOTTOM = 440;
const SAFE_RIGHT = 150;

export const InsightShort: React.FC<InsightProps> = (raw) => {
  const props = React.useMemo(() => deepClean(raw), [raw]);
  applyTheme(props.theme);
  useFonts();
  const {durationInFrames, width, fps} = useVideoConfig();
  const f = useCurrentFrame();
  const t = f / fps;
  const sc = props.scenes[0];
  if (!sc) return null;
  const ac = tone(sc.project?.color) || accentDefault();
  const title = (props.shortTitle || sc.heading || '').replace(/(…|\.\.\.)\s*$/, '');
  const hook = (props.shortHook || '').replace(/(…|\.\.\.)\s*$/, '');
  // 1-2 giây đầu: câu hook gây sốc, chữ to (≥ 64px), hiện ĐỦ ngay khung đầu tiên
  const HOOK_END = 1.8;
  const hookO = hook ? interpolate(t, [HOOK_END - 0.3, HOOK_END], [1, 0], clamp) : 0;
  const bodyO = hook ? interpolate(t, [HOOK_END - 0.3, HOOK_END], [0, 1], clamp) : 1;
  const tail = t > durationInFrames / fps - 3;
  return (
    <AccentCtx.Provider value={ac}>
      <AbsoluteFill style={{background: C.bg}}>
        {props.audio ? <Audio src={staticFile(props.audio)} /> : null}
        <Backdrop />
        <div style={{position: 'absolute', top: 110, left: 70, right: 70, display: 'flex', alignItems: 'center', gap: 16}}>
          <Img src={staticFile('logo.png')} style={{width: 60, height: 60, borderRadius: 99}} />
          <div style={{fontFamily: FONT}}>
            <div style={{fontFamily: HEAD, fontWeight: 700, color: C.ink, fontSize: 28, letterSpacing: 2}}>{(props.brand.name || '').toUpperCase()}</div>
            {sc.source ? <div style={{color: C.muted, fontWeight: 600, fontSize: 22}}>Source: <span style={{color: C.ink}}>{sc.source}</span></div> : null}
          </div>
        </div>
        <AbsoluteFill style={{opacity: bodyO}}>
          <div style={{position: 'absolute', top: 220, left: 70, right: 70, display: 'flex', flexDirection: 'column', gap: 22}}>
            {sc.project?.name ? <div><Chip text={sc.project.name} size={28} /></div> : null}
            <div style={{fontFamily: HEAD, fontWeight: 700, color: C.ink, lineHeight: 1.16, letterSpacing: -0.5,
              fontSize: fitSize(title, 940, sc.project?.name ? 250 : 320, 66, 40)}}>{title}</div>
          </div>
          <div style={{position: 'absolute', top: sc.project?.name ? 600 : 540, left: 70}}>
            <BeatStage sc={sc} data={props.data} post={props.post} w={940} h={640} />
          </div>
          <div style={{position: 'absolute', top: sc.project?.name ? 1272 : 1212, left: 0, right: 0, display: 'flex', justifyContent: 'center', opacity: tail ? 1 : 0.85}}>
            <Chip text="Xem full trên YouTube · Smart Penguin Insights" color={C.red} size={tail ? 28 : 24} />
          </div>
        </AbsoluteFill>
        {hookO > 0 ? (
          <AbsoluteFill style={{opacity: hookO, alignItems: 'center', justifyContent: 'center', padding: '260px 70px 520px'}}>
            <div style={{position: 'absolute', left: 0, right: 0, top: 200, bottom: 0, background: C.bg, opacity: 0.9}} />
            <div style={{position: 'relative', width: 940}}>
              <StatText text={hook} stat={(hook.match(/[$]?\d+(?:[.,]\d+)?\s*[%xKMBT]?/) || [''])[0]} size={fitSize(hook, 940, 760, 118, 64)} />
            </div>
          </AbsoluteFill>
        ) : null}
        <Captions words={sc.words} bottom={SAFE_BOTTOM} left={40} right={SAFE_RIGHT} size={46} maxWidth={860} perChunk={8} emph={sc.emph} subs={sc.subs} />
        <div style={{position: 'absolute', left: 0, bottom: 0, height: 8, width: (f / durationInFrames) * width, background: ac}} />
        <Handle size={30} style={{position: 'absolute', right: 40, top: 36}} />
      </AbsoluteFill>
    </AccentCtx.Provider>
  );
};
