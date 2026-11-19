import React from 'react';
import {AbsoluteFill, Audio, Img, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Backdrop, C, Captions, Chip, clamp, CountUp, FONT, Glitch, ImageDeck, RevealWords, useFonts, useSpring, Word} from './ui';
import {DataPanel, DataSpec} from './data';

export type Post = {author: string; handle: string; avatar?: string; cover?: string; title?: string; text?: string;
  likes?: number; views?: number; retweets?: number};
export type Scene = {
  type: 'hook' | 'intro' | 'section' | 'outro';
  from: number; dur: number; words: Word[];
  hook?: string; stat?: string; label?: string; images?: string[];
  title?: string; theme?: string;
  idx?: number; total?: number; heading?: string; keyStat?: string; keyLabel?: string; bullets?: string[];
  quote?: string; source?: string; data?: DataSpec | null; points?: string[];
};
export type InsightProps = {fps: number; width: number; height: number; audio: string; music?: string; duration: number;
  scenes: Scene[]; post: Post | null; brand: Record<string, string>; data?: any; logo?: string; mode?: string};

const fmt = (n?: number) => (n == null ? '' : n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : n >= 1e3 ? (n / 1e3).toFixed(1) + 'K' : String(n));

// ---------- top bar ----------
const TopBar: React.FC<{label: string; idx?: number; total?: number; logo?: string; brand: string}> = ({label, idx, total, logo, brand}) => {
  const s = useSpring(2, 18);
  return (
    <div style={{position: 'absolute', top: 44, left: 80, right: 80, display: 'flex', alignItems: 'center', gap: 18,
      opacity: s, transform: `translateY(${(1 - s) * -30}px)`, fontFamily: FONT}}>
      {logo ? <Img src={staticFile(logo)} style={{width: 58, height: 58, borderRadius: 99, border: `2px solid ${C.violet}`}} /> : null}
      <div>
        <div style={{color: C.ink, fontWeight: 800, fontSize: 28, letterSpacing: 2}}>{brand}</div>
        <div style={{color: C.muted, fontWeight: 600, fontSize: 20}}>{label}</div>
      </div>
      <div style={{flex: 1}} />
      {total ? (
        <div style={{display: 'flex', gap: 8, alignItems: 'center'}}>
          {Array.from({length: total}, (_, i) => <div key={i} style={{width: i + 1 === idx ? 44 : 14, height: 8, borderRadius: 9,
            background: i + 1 <= (idx || 0) ? C.violet : 'rgba(255,255,255,0.18)', boxShadow: i + 1 === idx ? `0 0 16px ${C.violet}` : 'none'}} />)}
          <div style={{color: C.ink, fontWeight: 800, fontSize: 26, marginLeft: 12}}>{String(idx).padStart(2, '0')}<span style={{color: C.muted}}>/{String(total).padStart(2, '0')}</span></div>
        </div>
      ) : null}
    </div>
  );
};

// ---------- HOOK ----------
const HookScene: React.FC<{sc: Scene}> = ({sc}) => {
  const f = useCurrentFrame();
  const shake = f < 18 ? Math.sin(f * 2.3) * (18 - f) * 0.6 : 0;
  return (
    <AbsoluteFill>
      <Backdrop img={sc.images?.[0]} dim={0.55} accent={C.pink} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 30, transform: `translateX(${shake}px)`}}>
        {sc.stat ? <CountUp value={sc.stat} size={250} delay={4} /> : null}
        {sc.label ? <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 40, color: C.cyan, letterSpacing: 6, textTransform: 'uppercase'}}>{sc.label}</div> : null}
        <div style={{maxWidth: 1500, textAlign: 'center', display: 'flex', justifyContent: 'center'}}>
          <RevealWords text={sc.hook || ''} size={sc.stat ? 64 : 92} delay={sc.stat ? 16 : 4} stagger={2} maxWidth={1500} />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------- INTRO with X post card ----------
const PostCard: React.FC<{post: Post; delay: number}> = ({post, delay}) => {
  const f = useCurrentFrame();
  const s = useSpring(delay, 16);
  const ry = interpolate(s, [0, 1], [35, 10]) + 2 * Math.sin(f / 40);
  return (
    <div style={{perspective: 1800}}>
      <div style={{width: 760, borderRadius: 32, background: 'rgba(16,14,30,0.92)', border: `2px solid ${C.violet}88`,
        boxShadow: `0 50px 140px rgba(0,0,0,0.7), 0 0 80px ${C.violet}44`, overflow: 'hidden', fontFamily: FONT,
        transform: `rotateY(-${ry}deg) rotateX(4deg) translateX(${(1 - s) * 300}px)`, opacity: s}}>
        {post.cover ? <Img src={staticFile(post.cover)} style={{width: '100%', height: 300, objectFit: 'cover'}} /> : null}
        <div style={{padding: 34}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
            {post.avatar ? <Img src={staticFile(post.avatar)} style={{width: 76, height: 76, borderRadius: 99}} /> : null}
            <div>
              <div style={{color: C.ink, fontSize: 32, fontWeight: 800}}>{post.author}</div>
              <div style={{color: C.muted, fontSize: 24, fontWeight: 600}}>@{post.handle}</div>
            </div>
            <div style={{flex: 1}} />
            <div style={{color: C.ink, fontSize: 44, fontWeight: 800}}>𝕏</div>
          </div>
          {post.title ? <div style={{color: C.ink, fontSize: 38, fontWeight: 800, marginTop: 22, lineHeight: 1.2}}>{post.title}</div> : null}
          <div style={{display: 'flex', gap: 34, marginTop: 22, color: C.muted, fontSize: 24, fontWeight: 600}}>
            {post.views ? <span>👁 {fmt(post.views)}</span> : null}
            {post.likes ? <span>♥ {fmt(post.likes)}</span> : null}
            {post.retweets ? <span>⟲ {fmt(post.retweets)}</span> : null}
          </div>
        </div>
      </div>
    </div>
  );
};

const IntroScene: React.FC<{sc: Scene; post: Post | null}> = ({sc, post}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  const agendaAt = Math.min(12, sc.dur * 0.4);
  const out = interpolate(t - agendaAt, [0, 0.6], [1, 0], clamp);
  return (
  <AbsoluteFill>
    <Backdrop img={sc.images?.[0]} />
    <AbsoluteFill style={{flexDirection: 'row', alignItems: 'center', padding: '0 110px', gap: 70}}>
      <div style={{flex: 1, position: 'relative', height: 700}}>
        <div style={{position: 'absolute', top: 60, display: 'flex', flexDirection: 'column', gap: 28, opacity: out, transform: `translateY(${(1 - out) * -30}px)`}}>
          <div><Chip text={`INSIGHT · ${(sc.theme || '').toUpperCase()}`} color={C.cyan} /></div>
          <RevealWords text={sc.title || ''} size={72} delay={6} stagger={3} maxWidth={900} />
          {post ? <div style={{fontFamily: FONT, color: C.muted, fontSize: 30, fontWeight: 600}}>Ý tưởng gốc từ bài viết của <span style={{color: C.ink}}>@{post.handle}</span></div> : null}
        </div>
        {t >= agendaAt ? (
          <Sequence from={Math.round(agendaAt * fps)} layout="none">
            <div style={{position: 'absolute', top: 60, display: 'flex', flexDirection: 'column', gap: 26}}>
              <div><Chip text={`${(sc.points || []).length} INSIGHT HÔM NAY`} color={C.gold} /></div>
              {(sc.points || []).map((p, i) => {
                const s = interpolate(f - Math.round(agendaAt * fps) - 8 - i * 10, [0, 14], [0, 1], clamp);
                return <div key={i} style={{display: 'flex', gap: 22, alignItems: 'center', opacity: s, transform: `translateX(${(1 - s) * -40}px)`,
                  fontFamily: FONT, fontWeight: 700, fontSize: 40, color: C.ink, maxWidth: 900}}>
                  <span style={{fontWeight: 800, color: 'transparent', WebkitTextStroke: `2px ${C.violet}`, fontSize: 54, width: 80}}>{String(i + 1).padStart(2, '0')}</span>{p}</div>;
              })}
            </div>
          </Sequence>
        ) : null}
      </div>
      {post ? <PostCard post={post} delay={14} /> : <ImageDeck images={sc.images || []} dur={sc.dur} w={760} h={560} />}
    </AbsoluteFill>
  </AbsoluteFill>
  );
};

// ---------- SECTION ----------
const Bullets: React.FC<{items: string[]; dur: number; fps: number}> = ({items, dur, fps}) => {
  const f = useCurrentFrame();
  return (
    <div style={{display: 'flex', flexDirection: 'column', gap: 22}}>
      {items.map((b, i) => {
        const at = Math.round(fps * (1.2 + (dur * 0.62 * i) / Math.max(1, items.length)));
        const s = interpolate(f - at, [0, 14], [0, 1], clamp);
        const live = f >= at;
        return (
          <div key={i} style={{display: 'flex', alignItems: 'center', gap: 20, opacity: s, transform: `translateX(${(1 - s) * -60}px)`,
            fontFamily: FONT, fontSize: 38, fontWeight: 700, color: C.ink}}>
            <div style={{width: 46, height: 46, borderRadius: 14, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: live ? C.violet : 'transparent', border: `2px solid ${C.violet}`, color: '#fff', fontSize: 28, fontWeight: 800,
              boxShadow: `0 0 20px ${C.violet}88`}}>{i + 1}</div>
            <span style={{textShadow: '0 4px 20px rgba(0,0,0,0.6)'}}>{b}</span>
          </div>
        );
      })}
    </div>
  );
};

const QuoteCard: React.FC<{post: Post | null; quote: string; w: number; h: number}> = ({post, quote, w, h}) => {
  const s = useSpring(4, 15);
  return (
    <div style={{width: w, height: h, borderRadius: 34, background: 'rgba(14,12,28,0.94)', border: `2px solid ${C.violet}88`, boxSizing: 'border-box',
      padding: 50, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 30, fontFamily: FONT, opacity: s,
      transform: `scale(${0.92 + 0.08 * s})`, boxShadow: `0 40px 120px rgba(0,0,0,0.6), 0 0 60px ${C.violet}44`}}>
      <div style={{fontSize: 140, lineHeight: 0.5, color: C.violet, fontWeight: 800}}>“</div>
      <div style={{fontSize: 46, lineHeight: 1.25, color: C.ink, fontWeight: 700}}>{quote}</div>
      {post ? <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
        {post.avatar ? <Img src={staticFile(post.avatar)} style={{width: 60, height: 60, borderRadius: 99}} /> : null}
        <div style={{color: C.muted, fontSize: 26, fontWeight: 600}}>ý tưởng từ <b style={{color: C.ink}}>@{post.handle}</b> · diễn giải lại</div>
      </div> : null}
    </div>
  );
};

const SectionScene: React.FC<{sc: Scene; data: any; brandName: string; mode?: string; post?: Post | null}> = ({sc, data, brandName, mode, post}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const numS = useSpring(0, 20);
  const hasData = !!(sc.data && sc.data.type && sc.data.type !== 'none');
  const dataMode = mode === 'data';
  // motion: nửa đầu ảnh, nửa sau hình dữ liệu · data: hình dữ liệu ngay, nửa sau trích ý tác giả
  const swapAt = dataMode ? 0 : sc.dur * 0.5;
  const quoteAt = sc.dur * 0.55;
  const t = f / fps;
  const showData = hasData && t >= swapAt;
  const dataIn = interpolate(t - swapAt, [0, 0.7], [0, 1], clamp);
  return (
    <AbsoluteFill>
      <Backdrop img={dataMode ? undefined : sc.images?.[0]} dim={0.86} accent={dataMode ? C.cyan : C.violet} />
      <TopBar label={sc.source ? `Insight · theo ${sc.source}` : 'Insight'} idx={sc.idx} total={sc.total} brand={brandName} logo="logo.png" />
      {/* big outlined chapter number */}
      <div style={{position: 'absolute', left: 110, top: 150, display: 'flex', alignItems: 'center', gap: 18, opacity: numS,
        transform: `translateX(${(1 - numS) * -40}px)`, fontFamily: FONT}}>
        <div style={{fontWeight: 800, fontSize: 96, lineHeight: 1, color: 'transparent', WebkitTextStroke: `2.5px ${C.violet}`,
          textShadow: `0 0 30px ${C.violet}66`}}>{String(sc.idx).padStart(2, '0')}</div>
        <div style={{width: 80 * numS, height: 4, borderRadius: 4, background: `linear-gradient(90deg, ${C.violet}, ${C.cyan})`}} />
        <div style={{color: C.cyan, fontWeight: 700, fontSize: 24, letterSpacing: 4}}>INSIGHT</div>
      </div>
      <div style={{position: 'absolute', left: 110, top: 290, width: 820, display: 'flex', flexDirection: 'column', gap: 40}}>
        <RevealWords text={sc.heading || ''} size={62} delay={6} stagger={3} maxWidth={820} highlight={sc.keyStat ? [sc.keyStat] : []} />
        {sc.bullets?.length ? <Bullets items={sc.bullets} dur={sc.dur} fps={fps} /> : null}
      </div>
      <div style={{position: 'absolute', right: 100, top: 190}}>
        {dataMode ? (
          <>
            <div style={{position: 'absolute', right: 0, top: 0, opacity: hasData && sc.quote ? interpolate(t - quoteAt, [0, 0.6], [1, 0], clamp) : 1}}>
              {hasData ? <DataPanel spec={sc.data!} data={data} w={820} h={540} /> : <QuoteCard post={post || null} quote={sc.quote || sc.heading || ''} w={820} h={540} />}
            </div>
            {hasData && sc.quote && t >= quoteAt ? (
              <div style={{position: 'absolute', right: 0, top: 0}}>
                <Sequence from={Math.round(quoteAt * fps)} layout="none"><QuoteCard post={post || null} quote={sc.quote} w={820} h={540} /></Sequence>
              </div>
            ) : null}
          </>
        ) : (
          <>
            <div style={{opacity: showData ? 1 - dataIn : 1, position: 'absolute', right: 0, top: 0}}>
              <ImageDeck images={sc.images || []} dur={hasData ? swapAt : sc.dur} w={820} h={540} every={4} />
            </div>
            {hasData ? (
              <div style={{opacity: dataIn, transform: `translateY(${(1 - dataIn) * 40}px) scale(${0.95 + 0.05 * dataIn})`, position: 'absolute', right: 0, top: 0}}>
                {showData ? <Sequence from={Math.round(swapAt * fps)} layout="none"><DataPanel spec={sc.data!} data={data} w={820} h={540} /></Sequence> : null}
              </div>
            ) : null}
          </>
        )}
        {sc.keyStat ? (
          <div style={{position: 'absolute', right: 0, top: 570, padding: '14px 30px', display: 'flex', alignItems: 'center', gap: 22, borderRadius: 24, background: 'rgba(12,10,24,0.92)',
            border: `2px solid ${C.gold}99`, boxShadow: `0 0 40px ${C.gold}44`, minWidth: 260}}>
            <CountUp value={sc.keyStat} size={64} delay={20} />
            <div style={{fontFamily: FONT, color: C.muted, fontWeight: 600, fontSize: 24, width: 330, lineHeight: 1.25}}>{sc.keyLabel}</div>
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

// ---------- OUTRO ----------
const OutroScene: React.FC<{sc: Scene; brandName: string}> = ({sc, brandName}) => {
  const f = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const pulse = 1 + 0.04 * Math.sin(f / 6);
  const btn = useSpring(Math.round(fps * Math.max(1, sc.dur - 4)), 12);
  return (
    <AbsoluteFill>
      <Backdrop accent={C.cyan} />
      <AbsoluteFill style={{padding: '150px 140px', flexDirection: 'column', gap: 34}}>
        <Chip text="TÓM LẠI" color={C.gold} />
        {(sc.points || []).map((p, i) => {
          const s = interpolate(f - 10 - i * 12, [0, 14], [0, 1], clamp);
          return <div key={i} style={{display: 'flex', gap: 24, alignItems: 'center', opacity: s, transform: `translateX(${(1 - s) * -50}px)`,
            fontFamily: FONT, fontWeight: 800, fontSize: 52, color: C.ink}}>
            <span style={{color: C.violet}}>{String(i + 1).padStart(2, '0')}</span>{p}</div>;
        })}
      </AbsoluteFill>
      <div style={{position: 'absolute', right: 140, bottom: 300, opacity: btn, transform: `scale(${btn * pulse})`, fontFamily: FONT,
        padding: '26px 54px', borderRadius: 99, background: C.red, color: '#fff', fontWeight: 800, fontSize: 44,
        boxShadow: `0 0 60px ${C.red}99`}}>ĐĂNG KÝ · {brandName}</div>
    </AbsoluteFill>
  );
};

// ---------- progress + watermark ----------
const Chrome: React.FC = () => {
  const f = useCurrentFrame();
  const {durationInFrames, width} = useVideoConfig();
  return (
    <>
      <div style={{position: 'absolute', left: 0, bottom: 0, height: 7, width: (f / durationInFrames) * width,
        background: `linear-gradient(90deg, ${C.violet}, ${C.cyan})`, boxShadow: `0 0 18px ${C.cyan}`}} />
      <div style={{position: 'absolute', right: 40, bottom: 26, fontFamily: FONT, fontWeight: 700, fontSize: 24,
        color: 'rgba(255,255,255,0.55)'}}>@Trong0322</div>
    </>
  );
};

export const Insight: React.FC<InsightProps> = (props) => {
  useFonts();
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{background: C.bg}}>
      {props.audio ? <Audio src={staticFile(props.audio)} /> : null}
      {props.music ? <Audio src={staticFile(props.music)} volume={0.12} /> : null}
      {props.scenes.map((sc, i) => (
        <Sequence key={i} from={Math.round(sc.from * fps)} durationInFrames={Math.max(1, Math.round(sc.dur * fps))}>
          {sc.type === 'hook' ? <HookScene sc={sc} /> : null}
          {sc.type === 'intro' ? <IntroScene sc={sc} post={props.post} /> : null}
          {sc.type === 'section' ? <SectionScene sc={sc} data={props.data} brandName={(props.brand.name || 'SMART PENGUIN INSIGHTS').toUpperCase()} mode={props.mode} post={props.post} /> : null}
          {sc.type === 'outro' ? <OutroScene sc={sc} brandName={(props.brand.name || 'SMART PENGUIN INSIGHTS').toUpperCase()} /> : null}
          {sc.type !== 'hook' ? <Captions words={sc.words} bottom={70} size={44} maxWidth={1500} /> : null}
          {i > 0 ? <Glitch /> : null}
        </Sequence>
      ))}
      <Chrome />
    </AbsoluteFill>
  );
};
