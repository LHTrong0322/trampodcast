import React from 'react';
import {AbsoluteFill, Audio, Img, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {AccentCtx, tone, Backdrop, C, Captions, Chip, clamp, CountUp, FONT, Glitch, RevealWords, useAccent, useFonts, useSpring, Word} from './ui';
import {DataPanel, DataSpec} from './data';

export type Post = {author: string; handle: string; avatar?: string; cover?: string; title?: string; text?: string;
  likes?: number; views?: number; retweets?: number};
export type Project = {name?: string; ticker?: string; logo?: string | null; color?: string | null};
export type Scene = {
  type: 'hook' | 'intro' | 'section' | 'outro';
  from: number; dur: number; words: Word[];
  hook?: string; stat?: string; label?: string; images?: string[];
  title?: string; theme?: string;
  idx?: number; total?: number; heading?: string; keyStat?: string; keyLabel?: string; bullets?: string[];
  quote?: string; source?: string; data?: DataSpec | null; points?: string[]; project?: Project | null;
};
export type InsightProps = {fps: number; width: number; height: number; audio: string; music?: string; duration: number;
  scenes: Scene[]; post: Post | null; brand: Record<string, string>; data?: any; logo?: string; mode?: string; shortTitle?: string};

export const DEFAULT_ACCENT = '#4F5BD5';
const fmt = (n?: number) => (n == null ? '' : n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : n >= 1e3 ? (n / 1e3).toFixed(1) + 'K' : String(n));

// ---------- thanh trên: logo kênh + nguồn ----------
const TopBar: React.FC<{source?: string; idx?: number; total?: number; brand: string; project?: Project | null}> = ({source, idx, total, brand, project}) => {
  const s = useSpring(2, 18);
  const ac = useAccent();
  return (
    <div style={{position: 'absolute', top: 44, left: 80, right: 80, display: 'flex', alignItems: 'center', gap: 18,
      opacity: s, transform: `translateY(${(1 - s) * -20}px)`, fontFamily: FONT}}>
      <Img src={staticFile('logo.png')} style={{width: 54, height: 54, borderRadius: 99, border: `1.5px solid ${C.line}`}} />
      <div>
        <div style={{color: C.ink, fontWeight: 800, fontSize: 24, letterSpacing: 2}}>{brand}</div>
        {source ? <div style={{color: C.muted, fontWeight: 600, fontSize: 19}}>Source: <span style={{color: C.ink}}>{source}</span></div> : null}
      </div>
      <div style={{flex: 1}} />
      {project?.name ? (
        <div style={{display: 'flex', alignItems: 'center', gap: 12, padding: '8px 18px', borderRadius: 99, background: `${ac}1A`,
          border: `1.5px solid ${ac}66`, marginRight: 24}}>
          {project.logo ? <Img src={staticFile(project.logo)} style={{width: 32, height: 32, borderRadius: 99}} /> : null}
          <span style={{color: C.ink, fontWeight: 700, fontSize: 22}}>{project.name}</span>
        </div>
      ) : null}
      {total ? (
        <div style={{display: 'flex', gap: 8, alignItems: 'center'}}>
          {Array.from({length: total}, (_, i) => <div key={i} style={{width: i + 1 === idx ? 14 : 10, height: i + 1 === idx ? 14 : 10, borderRadius: 99,
            background: i + 1 <= (idx || 0) ? ac : 'rgba(25,35,80,0.15)'}} />)}
          <div style={{color: C.ink, fontWeight: 800, fontSize: 24, marginLeft: 10}}>{String(idx).padStart(2, '0')}<span style={{color: C.muted}}>/{String(total).padStart(2, '0')}</span></div>
        </div>
      ) : null}
    </div>
  );
};

// ---------- HOOK ----------
const HookScene: React.FC<{sc: Scene}> = ({sc}) => {
  const f = useCurrentFrame();
  const zoom = 1 + Math.min(f, 600) * 0.00012;   // zoom chậm cho có chuyển động (review 1518)
  return (
  <AbsoluteFill>
    <Backdrop img={sc.images?.[0]} dim={0.7} />
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 26, transform: `scale(${zoom})`}}>
      {sc.stat ? <CountUp value={sc.stat} size={220} delay={4} /> : null}
      {sc.label ? <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 36, color: C.muted, letterSpacing: 4, textTransform: 'uppercase'}}>{sc.label}</div> : null}
      <div style={{maxWidth: 1500, textAlign: 'center', display: 'flex', justifyContent: 'center'}}>
        <RevealWords text={sc.hook || ''} size={sc.stat ? 66 : 96} delay={sc.stat ? 16 : 2} stagger={2} maxWidth={1560} />
      </div>
    </AbsoluteFill>
  </AbsoluteFill>
  );
};

// ---------- thẻ bài X ----------
const PostCard: React.FC<{post: Post; delay: number}> = ({post, delay}) => {
  const f = useCurrentFrame();
  const s = useSpring(delay, 18);
  return (
    <div style={{perspective: 1800}}>
      <div style={{width: 740, borderRadius: 26, background: C.panel, border: `1px solid ${C.line}`,
        boxShadow: '0 18px 50px rgba(40,50,110,0.12)', overflow: 'hidden', fontFamily: FONT,
        transform: `rotateY(${interpolate(s, [0, 1], [-25, -6]) + Math.sin(f / 50)}deg) translateX(${(1 - s) * 200}px)`, opacity: s}}>
        {post.cover ? <Img src={staticFile(post.cover)} style={{width: '100%', height: 280, objectFit: 'cover'}} /> : null}
        <div style={{padding: 32}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            {post.avatar ? <Img src={staticFile(post.avatar)} style={{width: 68, height: 68, borderRadius: 99}} /> : null}
            <div>
              <div style={{color: C.ink, fontSize: 30, fontWeight: 800}}>{post.author}</div>
              <div style={{color: C.muted, fontSize: 22, fontWeight: 600}}>@{post.handle}</div>
            </div>
            <div style={{flex: 1}} />
            <div style={{color: C.ink, fontSize: 40, fontWeight: 800}}>𝕏</div>
          </div>
          {post.title ? <div style={{color: C.ink, fontSize: 34, fontWeight: 800, marginTop: 20, lineHeight: 1.2}}>{post.title}</div> : null}
          <div style={{display: 'flex', gap: 30, marginTop: 18, color: C.muted, fontSize: 22, fontWeight: 600}}>
            {post.views ? <span>{fmt(post.views)} views</span> : null}
            {post.likes ? <span>{fmt(post.likes)} likes</span> : null}
            {post.retweets ? <span>{fmt(post.retweets)} reposts</span> : null}
          </div>
        </div>
      </div>
    </div>
  );
};

// ---------- INTRO: tiêu đề → danh sách insight ----------
const IntroScene: React.FC<{sc: Scene; post: Post | null}> = ({sc, post}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = useAccent();
  const t = f / fps;
  const agendaAt = Math.min(6, sc.dur * 0.3);   // review 1518: thẻ giới thiệu kênh ngắn lại
  const out = interpolate(t - agendaAt, [0, 0.5], [1, 0], clamp);
  return (
    <AbsoluteFill>
      <Backdrop img={sc.images?.[0]} dim={0.88} />
      <AbsoluteFill style={{flexDirection: 'row', alignItems: 'center', padding: '0 110px', gap: 70}}>
        <div style={{flex: 1, position: 'relative', height: 700}}>
          {/* Trọng 21/11: câu chào mở đầu phải có logo kênh */}
          <div style={{position: 'absolute', top: 0, display: 'flex', alignItems: 'center', gap: 22,
            opacity: interpolate(t, [0.1, 0.6], [0, 1], clamp), transform: `scale(${interpolate(t, [0.1, 0.6], [0.85, 1], clamp)})`, transformOrigin: 'left center'}}>
            <Img src={staticFile('logo.png')} style={{width: 112, height: 112, borderRadius: 999, boxShadow: `0 0 0 6px ${ac}33, 0 14px 40px rgba(40,50,110,0.18)`}} />
            <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
              <div style={{fontFamily: FONT, fontWeight: 800, fontSize: 40, letterSpacing: 2, color: C.ink}}>SMART PENGUIN INSIGHTS</div>
              <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 26, color: C.muted}}>@Trong0322</div>
            </div>
          </div>
          <div style={{position: 'absolute', top: 175, display: 'flex', flexDirection: 'column', gap: 28, opacity: out}}>
            <div><Chip text={(sc.theme || 'INSIGHT').toUpperCase()} /></div>
            <RevealWords text={sc.title || ''} size={70} delay={6} stagger={3} maxWidth={900} />
          </div>
          {t >= agendaAt ? (
            <Sequence from={Math.round(agendaAt * fps)} layout="none">
              <div style={{position: 'absolute', top: 165, display: 'flex', flexDirection: 'column', gap: 24}}>
                <div><Chip text={`${(sc.points || []).length} INSIGHT TRONG VIDEO`} /></div>
                {(sc.points || []).map((p, i) => {
                  // review 1915: hiện TỪNG DÒNG rải đều theo thời gian còn lại của phần mở đầu, không hiện cả bảng một lúc
                  const step = Math.max(9, Math.floor(((sc.dur - agendaAt) * fps - 20) / Math.max(1, (sc.points || []).length)));
                  const s = interpolate(f - Math.round(agendaAt * fps) - 8 - i * step, [0, 12], [0, 1], clamp);
                  return <div key={i} style={{display: 'flex', gap: 22, alignItems: 'baseline', opacity: s, transform: `translateX(${(1 - s) * -30}px)`,
                    fontFamily: FONT, fontWeight: 700, fontSize: 38, color: C.ink, maxWidth: 900, lineHeight: 1.25}}>
                    <span style={{fontWeight: 800, color: ac, fontSize: 34, width: 56, flexShrink: 0}}>{String(i + 1).padStart(2, '0')}</span>{p}</div>;
                })}
              </div>
            </Sequence>
          ) : null}
        </div>
        {post ? <PostCard post={post} delay={14} /> : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------- SECTION (kiểu "dữ liệu thật") ----------
const Bullets: React.FC<{items: string[]; dur: number; fps: number}> = ({items, dur, fps}) => {
  const f = useCurrentFrame();
  const ac = useAccent();
  return (
    <div style={{display: 'flex', flexDirection: 'column', gap: 20}}>
      {items.map((b, i) => {
        const at = Math.round(fps * (1.2 + (dur * 0.6 * i) / Math.max(1, items.length)));
        const s = interpolate(f - at, [0, 12], [0, 1], clamp);
        const nextAt = i + 1 < items.length ? Math.round(fps * (1.2 + (dur * 0.6 * (i + 1)) / items.length)) : 1e9;
        const active = f >= at && f < nextAt;   // dòng đang nói thì nổi bật, dòng cũ mờ đi (review 1518)
        return (
          <div key={i} style={{display: 'flex', alignItems: 'center', gap: 18, opacity: s * (active ? 1 : 0.55),
            transform: `translateX(${(1 - s) * -40}px) scale(${active ? 1.03 : 1})`, transformOrigin: 'left center',
            padding: '8px 16px', marginLeft: -16, borderRadius: 14, background: active ? `${ac}18` : 'transparent',
            fontFamily: FONT, fontSize: 34, fontWeight: active ? 700 : 600, color: C.ink}}>
            <div style={{width: 10, height: 10, borderRadius: 99, background: ac, flexShrink: 0}} />
            <span>{b}</span>
          </div>
        );
      })}
    </div>
  );
};

export const QuoteCard: React.FC<{post: Post | null; quote: string; w: number; h: number}> = ({post, quote, w, h}) => {
  const s = useSpring(4, 18);
  const ac = useAccent();
  return (
    <div style={{width: w, height: h, borderRadius: 26, background: C.panel, border: `1px solid ${C.line}`, boxSizing: 'border-box',
      padding: 50, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 26, fontFamily: FONT, opacity: s,
      transform: `scale(${0.96 + 0.04 * s})`, boxShadow: '0 18px 50px rgba(40,50,110,0.12)', borderLeft: `6px solid ${ac}`}}>
      <div style={{fontSize: 44, lineHeight: 1.3, color: C.ink, fontWeight: 700}}>“{quote}”</div>
      {post ? <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
        {post.avatar ? <Img src={staticFile(post.avatar)} style={{width: 52, height: 52, borderRadius: 99}} /> : null}
        <div style={{color: C.muted, fontSize: 24, fontWeight: 600}}>Source: <b style={{color: C.ink}}>@{post.handle}</b></div>
      </div> : null}
    </div>
  );
};

const SectionScene: React.FC<{sc: Scene; data: any; brandName: string; post?: Post | null}> = ({sc, data, brandName, post}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = useAccent();
  const t = f / fps;
  const numS = useSpring(0, 20);
  const hasData = !!(sc.data && sc.data.type && sc.data.type !== 'none');
  const quoteAt = sc.dur * 0.55;
  const toQuote = hasData && !!sc.quote;
  return (
    <AbsoluteFill>
      <Backdrop />
      <TopBar source={sc.source} idx={sc.idx} total={sc.total} brand={brandName} project={sc.project} />
      <div style={{position: 'absolute', left: 110, top: 170, display: 'flex', alignItems: 'center', gap: 16, opacity: numS, fontFamily: FONT}}>
        <div style={{fontWeight: 800, fontSize: 30, color: ac}}>{String(sc.idx).padStart(2, '0')}</div>
        <div style={{width: 10, height: 10, borderRadius: 99, background: ac, transform: `scale(${numS})`}} />
        <div style={{color: C.muted, fontWeight: 700, fontSize: 22, letterSpacing: 4}}>INSIGHT</div>
      </div>
      <div style={{position: 'absolute', left: 110, top: 230, width: 800, display: 'flex', flexDirection: 'column', gap: 40}}>
        <RevealWords text={sc.heading || ''} size={58} delay={6} stagger={3} maxWidth={800}
          highlight={[sc.project?.name || '', sc.keyStat || ''].filter(Boolean)} />
        {sc.bullets?.length ? <Bullets items={sc.bullets} dur={sc.dur} fps={fps} /> : null}
      </div>
      <div style={{position: 'absolute', right: 100, top: 190, width: 840, height: 560,
        transform: `scale(${1 + Math.min(t, 40) * 0.0015}) translateY(${-Math.min(t, 40) * 0.4}px)`, transformOrigin: 'center'}}>
        <div style={{position: 'absolute', inset: 0, opacity: toQuote ? interpolate(t - quoteAt, [0, 0.5], [1, 0], clamp) : 1}}>
          {hasData ? <DataPanel spec={sc.data!} data={data} w={840} h={560} />
            : <QuoteCard post={post || null} quote={sc.quote || sc.heading || ''} w={840} h={560} />}
        </div>
        {toQuote && t >= quoteAt ? (
          <div style={{position: 'absolute', inset: 0}}>
            <Sequence from={Math.round(quoteAt * fps)} layout="none"><QuoteCard post={post || null} quote={sc.quote!} w={840} h={560} /></Sequence>
          </div>
        ) : null}
        {sc.keyStat ? (
          <div style={{position: 'absolute', right: 0, top: 590, padding: '14px 28px', display: 'flex', alignItems: 'center', gap: 20,
            borderRadius: 18, background: C.panel, border: `1px solid ${C.line}`}}>
            <div style={{whiteSpace: 'nowrap'}}><CountUp value={sc.keyStat} size={sc.keyStat.length > 6 ? 44 : 58} delay={20} /></div>
            <div style={{fontFamily: FONT, color: C.muted, fontWeight: 600, fontSize: 22, width: 320, lineHeight: 1.25}}>{sc.keyLabel}</div>
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

// ---------- OUTRO (giữ như bản 1+2) ----------
const OutroScene: React.FC<{sc: Scene; brandName: string}> = ({sc, brandName}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = useAccent();
  const pulse = 1 + 0.03 * Math.sin(f / 6);
  const btn = useSpring(Math.round(fps * Math.max(1, sc.dur - 4)), 12);
  return (
    <AbsoluteFill>
      <Backdrop />
      <AbsoluteFill style={{padding: '150px 140px', flexDirection: 'column', gap: 32}}>
        <div><Chip text="TÓM LẠI" /></div>
        {(sc.points || []).map((p, i) => {
          const s = interpolate(f - 10 - i * 12, [0, 14], [0, 1], clamp);
          return <div key={i} style={{display: 'flex', gap: 24, alignItems: 'baseline', opacity: s, transform: `translateX(${(1 - s) * -40}px)`,
            fontFamily: FONT, fontWeight: 800, fontSize: 48, color: C.ink}}>
            <span style={{color: ac}}>{String(i + 1).padStart(2, '0')}</span>{p}</div>;
        })}
      </AbsoluteFill>
      <div style={{position: 'absolute', right: 140, bottom: 300, opacity: btn, transform: `scale(${btn * pulse})`, fontFamily: FONT,
        padding: '24px 50px', borderRadius: 99, background: C.red, color: '#fff', fontWeight: 800, fontSize: 40}}>ĐĂNG KÝ · {brandName}</div>
    </AbsoluteFill>
  );
};

const Chrome: React.FC = () => {
  const f = useCurrentFrame();
  const {durationInFrames, width} = useVideoConfig();
  const ac = useAccent();
  return (
    <>
      <div style={{position: 'absolute', left: 0, bottom: 0, height: 5, width: (f / durationInFrames) * width, background: ac}} />
      <div style={{position: 'absolute', right: 40, bottom: 24, fontFamily: FONT, fontWeight: 700, fontSize: 22,
        color: 'rgba(19,24,54,0.55)'}}>@Trong0322</div>
    </>
  );
};

export const Insight: React.FC<InsightProps> = (props) => {
  useFonts();
  const {fps} = useVideoConfig();
  const f = useCurrentFrame();
  const brandName = (props.brand.name || 'SMART PENGUIN INSIGHTS').toUpperCase();
  const cur = props.scenes.find((s) => f >= Math.round(s.from * fps) && f < Math.round((s.from + s.dur) * fps));
  return (
    <AbsoluteFill style={{background: C.bg}}>
      {props.audio ? <Audio src={staticFile(props.audio)} /> : null}
      {props.scenes.map((sc, i) => (
        <Sequence key={i} from={Math.round(sc.from * fps)} durationInFrames={Math.max(1, Math.round(sc.dur * fps))}>
          <AccentCtx.Provider value={tone(sc.project?.color || DEFAULT_ACCENT)}>
            {sc.type === 'hook' ? <HookScene sc={sc} /> : null}
            {sc.type === 'intro' ? <IntroScene sc={sc} post={props.post} /> : null}
            {sc.type === 'section' ? <SectionScene sc={sc} data={props.data} brandName={brandName} post={props.post} /> : null}
            {sc.type === 'outro' ? <OutroScene sc={sc} brandName={brandName} /> : null}
            {sc.type !== 'hook' ? <Captions words={sc.words} bottom={60} size={46} maxWidth={1560} perChunk={10} /> : null}
            {i > 0 ? <Glitch /> : null}
          </AccentCtx.Provider>
        </Sequence>
      ))}
      <AccentCtx.Provider value={tone(cur?.project?.color || DEFAULT_ACCENT)}><Chrome /></AccentCtx.Provider>
    </AbsoluteFill>
  );
};
