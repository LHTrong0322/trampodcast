import React from 'react';
import {AbsoluteFill, Audio, Img, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {AccentCtx, Backdrop, BRAND, glass, Handle, C, Captions, Chip, clamp, CountUp, DISPLAY, FONT, Glitch, HEAD, RevealWords, useAccent, useFonts, useSpring, Word} from './ui';
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
  endAt?: number; xquotes?: {text: string; vi?: string}[]; terms?: {term: string; explain: string; at: number}[];
};
export type InsightProps = {fps: number; width: number; height: number; audio: string; music?: string; duration: number;
  scenes: Scene[]; post: Post | null; brand: Record<string, string>; data?: any; logo?: string; mode?: string; shortTitle?: string};

export const DEFAULT_ACCENT = BRAND.blue;
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
        <div style={{color: C.ink, fontFamily: HEAD, fontWeight: 700, fontSize: 24, letterSpacing: 2}}>{brand}</div>
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
          {Array.from({length: total}, (_, i) => <div key={i} style={{width: i + 1 === idx ? 40 : 12, height: 6, borderRadius: 9,
            background: i + 1 <= (idx || 0) ? ac : 'rgba(255,255,255,0.15)'}} />)}
          <div style={{color: C.ink, fontFamily: DISPLAY, fontWeight: 800, fontSize: 22, marginLeft: 10}}>{String(idx).padStart(2, '0')}<span style={{color: C.muted}}>/{String(total).padStart(2, '0')}</span></div>
        </div>
      ) : null}
    </div>
  );
};

// ---------- HOOK ----------
const HookScene: React.FC<{sc: Scene; brand: string; source?: string}> = ({sc, brand, source}) => {
  const f = useCurrentFrame();
  const ring = (k: number) => {
    const t = ((f - 10 - k * 18) % 54) / 54;
    return f < 10 + k * 18 ? 0 : t;
  };
  return (
  <AbsoluteFill>
    <Backdrop img={sc.images?.[0]} dim={0.75} />
    <TopBar brand={brand} source={source} />
    {sc.stat ? [0, 1, 2].map((k) => <div key={k} style={{position: 'absolute', left: '50%', top: '34%', width: 900, height: 900,
      marginLeft: -450, marginTop: -450, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.5)',
      transform: `scale(${0.3 + ring(k) * 1.2})`, opacity: (1 - ring(k)) * 0.18}} />) : null}
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 26}}>
      {sc.stat ? <CountUp value={sc.stat} size={240} delay={3} color={BRAND.orange} frames={40} /> : null}
      {sc.label ? <div style={{fontFamily: HEAD, fontWeight: 700, fontSize: 34, color: C.muted, letterSpacing: 4, textTransform: 'uppercase'}}>{sc.label}</div> : null}
      <div style={{maxWidth: 1500, textAlign: 'center', display: 'flex', justifyContent: 'center'}}>
        <RevealWords text={sc.hook || ''} size={sc.stat ? 58 : 84} delay={sc.stat ? 22 : 4} stagger={2} maxWidth={1500} />
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
      <div style={{width: 740, borderRadius: 26, ...glass,
        boxShadow: '0 40px 100px rgba(0,0,0,0.55)', overflow: 'hidden', fontFamily: FONT,
        transform: `rotateY(${interpolate(s, [0, 1], [-25, -6]) + Math.sin(f / 50)}deg) translateX(${(1 - s) * 200}px)`, opacity: s}}>
        {post.cover ? <Img src={staticFile(post.cover)} style={{width: '100%', height: 280, objectFit: 'cover'}} /> : null}
        <div style={{padding: 32}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            {post.avatar ? <Img src={staticFile(post.avatar)} style={{width: 68, height: 68, borderRadius: 99}} /> : null}
            <div>
              <div style={{color: C.ink, fontFamily: HEAD, fontSize: 30, fontWeight: 700}}>{post.author}</div>
              <div style={{color: C.muted, fontSize: 22, fontWeight: 600}}>@{post.handle}</div>
            </div>
            <div style={{flex: 1}} />
            <div style={{color: C.ink, fontSize: 40, fontWeight: 800}}>𝕏</div>
          </div>
          {post.title ? <div style={{color: C.ink, fontFamily: HEAD, fontSize: 34, fontWeight: 700, marginTop: 20, lineHeight: 1.2}}>{post.title}</div> : null}
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
const IntroScene: React.FC<{sc: Scene; post: Post | null; brand: string}> = ({sc, post, brand}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = useAccent();
  const t = f / fps;
  const agendaAt = Math.min(11, sc.dur * 0.4);
  const out = interpolate(t - agendaAt, [0, 0.5], [1, 0], clamp);
  return (
    <AbsoluteFill>
      <Backdrop img={sc.images?.[0]} dim={0.88} />
      <TopBar brand={brand} source={post ? '@' + post.handle : undefined} />
      <AbsoluteFill style={{flexDirection: 'row', alignItems: 'center', padding: '60px 110px 0', gap: 70}}>
        <div style={{flex: 1, position: 'relative', height: 700}}>
          <div style={{position: 'absolute', top: 60, display: 'flex', flexDirection: 'column', gap: 28, opacity: out}}>
            <div><Chip text={(sc.theme || 'INSIGHT').toUpperCase()} /></div>
            <RevealWords text={sc.title || ''} size={70} delay={6} stagger={3} maxWidth={900} />
          </div>
          {t >= agendaAt ? (
            <Sequence from={Math.round(agendaAt * fps)} layout="none">
              <div style={{position: 'absolute', top: 60, display: 'flex', flexDirection: 'column', gap: 24}}>
                <div><Chip text={`${(sc.points || []).length} INSIGHT TRONG VIDEO`} /></div>
                {(sc.points || []).map((p, i, arr) => {
                  // hiện từng dòng một trong phần còn lại của intro, dòng đang nói sáng nhất
                  const span = Math.max(1, sc.dur - agendaAt - 1.5) / arr.length;
                  const at = Math.round((agendaAt + 0.4 + i * span) * fps);
                  const s = interpolate(f - at, [0, 10], [0, 1], clamp);
                  const cur = f >= at && (i === arr.length - 1 || f < Math.round((agendaAt + 0.4 + (i + 1) * span) * fps));
                  return <div key={i} style={{display: 'flex', gap: 22, alignItems: 'center', opacity: s * (cur ? 1 : 0.45),
                    transform: `translateX(${(1 - s) * -30}px) scale(${cur ? 1.03 : 1})`, transformOrigin: 'left center',
                    fontFamily: HEAD, fontWeight: 700, fontSize: 40, color: C.ink, maxWidth: 900, lineHeight: 1.2}}>
                    <span style={{fontFamily: DISPLAY, fontWeight: 800, color: cur ? BRAND.orange : ac, fontSize: 30, width: 64, flexShrink: 0}}>{String(i + 1).padStart(2, '0')}</span>{p}</div>;
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
    <div style={{display: 'flex', flexDirection: 'column', gap: 18}}>
      {items.map((b, i) => {
        const at = Math.round(fps * (1.2 + (dur * 0.6 * i) / Math.max(1, items.length)));
        const s = interpolate(f - at, [0, 12], [0, 1], clamp);
        return (
          <div key={i} style={{display: 'flex', alignItems: 'center', gap: 16, opacity: s, transform: `translateX(${(1 - s) * -40}px)`,
            fontFamily: FONT, fontSize: 32, fontWeight: 500, color: C.ink}}>
            <div style={{width: 10, height: 10, borderRadius: 3, background: ac, flexShrink: 0, transform: 'rotate(45deg)'}} />
            <span>{b}</span>
          </div>
        );
      })}
    </div>
  );
};

export const QuoteCard: React.FC<{post: Post | null; quote: string; w: number; h: number}> = ({post, quote, w, h}) => {
  const s = useSpring(2, 18);
  const ac = useAccent();
  return (
    <div style={{width: w, height: h, borderRadius: 26, ...glass, boxSizing: 'border-box',
      padding: 50, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 26, fontFamily: FONT, opacity: s,
      transform: `scale(${0.96 + 0.04 * s})`, boxShadow: '0 30px 80px rgba(0,0,0,0.4)', borderLeft: `6px solid ${ac}`}}>
      <div style={{fontFamily: HEAD, fontSize: 44, lineHeight: 1.28, color: C.ink, fontWeight: 700}}>“{quote}”</div>
      {post ? <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
        {post.avatar ? <Img src={staticFile(post.avatar)} style={{width: 52, height: 52, borderRadius: '50%'}} /> : null}
        <div style={{color: C.muted, fontSize: 24, fontWeight: 500}}>Source: <b style={{color: C.ink}}>@{post.handle}</b></div>
      </div> : null}
    </div>
  );
};

// thẻ trích nguyên văn câu highlight của tác giả trên X (kèm dịch)
const XQuoteCard: React.FC<{post: Post | null; text: string; vi?: string; w: number; h: number}> = ({post, text, vi, w, h}) => {
  const s = useSpring(2, 16);
  const ac = useAccent();
  return (
    <div style={{width: w, height: h, borderRadius: 26, ...glass, boxSizing: 'border-box',
      padding: '40px 46px', display: 'flex', flexDirection: 'column', gap: 22, fontFamily: FONT, opacity: s,
      transform: `translateY(${(1 - s) * 30}px)`, boxShadow: `0 30px 80px rgba(0,0,0,0.45), 0 0 0 1px ${ac}22`}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
        {post?.avatar ? <Img src={staticFile(post.avatar)} style={{width: 64, height: 64, borderRadius: '50%'}} /> : null}
        <div>
          <div style={{color: C.ink, fontFamily: HEAD, fontWeight: 700, fontSize: 28}}>{post?.author}</div>
          <div style={{color: C.muted, fontSize: 22}}>@{post?.handle}</div>
        </div>
        <div style={{flex: 1}} />
        <div style={{color: C.ink, fontSize: 38, fontWeight: 800}}>𝕏</div>
      </div>
      {/* hiện bản dịch tiếng Việt (giống video trước); câu gốc đã được kiểm tra có thật trong bài */}
      <div style={{fontFamily: HEAD, color: C.ink, fontSize: (vi || text).length > 130 ? 36 : 42, fontWeight: 600, lineHeight: 1.3}}>“{vi || text}”</div>
      <div style={{marginTop: 'auto', color: C.muted, fontSize: 22}}>Dịch từ bài viết của <b style={{color: C.ink}}>@{post?.handle}</b> trên X</div>
    </div>
  );
};

// chú thích nhanh thuật ngữ (FDV, Low Float…) hiện đúng lúc được nhắc
const TermCallout: React.FC<{terms: {term: string; explain: string; at: number}[]}> = ({terms}) => {
  const f = useCurrentFrame();
  const ac = useAccent();
  const {fps} = useVideoConfig();
  const t = f / fps;
  const cur = [...terms].reverse().find((x) => t >= x.at && t < x.at + 5.5);
  if (!cur) return null;
  const lt = t - cur.at;
  const o = interpolate(lt, [0, 0.25, 5.1, 5.5], [0, 1, 1, 0], clamp);
  return (
    <div style={{position: 'absolute', left: 110, top: 770, display: 'flex', alignItems: 'center', gap: 16, opacity: o,
      transform: `translateY(${(1 - o) * 16}px)`, padding: '14px 22px', borderRadius: 16, background: 'rgba(255,255,255,0.05)',
      border: `1px solid ${C.line}`, maxWidth: 820, fontFamily: FONT}}>
      <div style={{fontSize: 30}}>💡</div>
      <div style={{color: C.ink, fontSize: 25, lineHeight: 1.3}}><b style={{fontFamily: HEAD, color: ac}}>{cur.term}</b>: {cur.explain}</div>
    </div>
  );
};

type Beat = {kind: 'data' | 'x' | 'quote'; text?: string; vi?: string};

const SectionScene: React.FC<{sc: Scene; data: any; brandName: string; post?: Post | null}> = ({sc, data, brandName, post}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = useAccent();
  const t = f / fps;
  const numS = useSpring(0, 20);
  const hasData = !!(sc.data && sc.data.type && sc.data.type !== 'none');
  // các "nhịp hình" bên phải đổi liên tục (~8s/lần) để màn hình không đứng yên
  const beats: Beat[] = [];
  if (hasData) beats.push({kind: 'data'});
  (sc.xquotes || []).slice(0, 2).forEach((q) => beats.push({kind: 'x', text: q.text, vi: q.vi}));
  if (sc.quote && beats.length < 3) beats.push({kind: 'quote', text: sc.quote});
  if (!beats.length) beats.push({kind: 'quote', text: sc.heading});
  const per = Math.max(6, (sc.dur - 0.5) / beats.length);
  const bi = Math.min(beats.length - 1, Math.floor(t / per));
  const zoom = 1 + 0.025 * ((t % per) / per);
  const W = 840, H = 560;
  return (
    <AbsoluteFill>
      <Backdrop />
      <TopBar source={sc.source} idx={sc.idx} total={sc.total} brand={brandName} project={sc.project} />
      <div style={{position: 'absolute', left: 110, top: 170, display: 'flex', alignItems: 'center', gap: 16, opacity: numS}}>
        <div style={{fontFamily: DISPLAY, fontWeight: 800, fontSize: 28, color: ac}}>{String(sc.idx).padStart(2, '0')}</div>
        <div style={{width: 60 * numS, height: 3, borderRadius: 3, background: ac}} />
        <div style={{fontFamily: HEAD, color: C.muted, fontWeight: 700, fontSize: 22, letterSpacing: 4}}>INSIGHT</div>
      </div>
      <div style={{position: 'absolute', left: 110, top: 230, width: 800, display: 'flex', flexDirection: 'column', gap: 36}}>
        <RevealWords text={sc.heading || ''} size={58} delay={6} stagger={3} maxWidth={800}
          highlight={[sc.project?.name || '', sc.keyStat || ''].filter(Boolean)} />
        {sc.bullets?.length ? <Bullets items={sc.bullets} dur={sc.dur} fps={fps} /> : null}
      </div>
      {sc.terms?.length ? <TermCallout terms={sc.terms} /> : null}
      <div style={{position: 'absolute', right: 100, top: 190, width: W, height: H}}>
        {beats.map((b, i) => {
          if (Math.abs(i - bi) > 1) return null;
          const st = i * per;
          const o = i === bi ? (i === 0 ? 1 : interpolate(t - st, [0, 0.45], [0, 1], clamp)) : i === bi - 1 ? interpolate(t - st - per, [0, 0.45], [1, 0], clamp) : 0;
          if (o <= 0) return null;
          return (
            <div key={i} style={{position: 'absolute', inset: 0, opacity: o, transform: `scale(${i === bi ? zoom : 1}) translateX(${(1 - o) * (i === bi ? 40 : -40)}px)`}}>
              <Sequence from={Math.round(st * fps)} layout="none">
                {b.kind === 'data' ? <DataPanel spec={sc.data!} data={data} w={W} h={H} />
                  : b.kind === 'x' ? <XQuoteCard post={post || null} text={b.text!} vi={b.vi} w={W} h={H} />
                    : <QuoteCard post={post || null} quote={b.text || ''} w={W} h={H} />}
              </Sequence>
            </div>
          );
        })}
        {sc.keyStat ? (
          <div style={{position: 'absolute', right: 0, top: 590, padding: '14px 28px', display: 'flex', alignItems: 'center', gap: 20,
            borderRadius: 18, ...glass}}>
            <div style={{whiteSpace: 'nowrap'}}><CountUp value={sc.keyStat} size={sc.keyStat.length > 6 ? 40 : 54} delay={20} color={BRAND.orange} /></div>
            <div style={{fontFamily: FONT, color: C.muted, fontWeight: 500, fontSize: 22, width: 320, lineHeight: 1.25}}>{sc.keyLabel}</div>
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

// ---------- OUTRO: tóm lại → màn hình kết thúc (chừa chỗ gắn 2 video + nút đăng ký của YouTube) ----------
const OutroScene: React.FC<{sc: Scene; brandName: string}> = ({sc, brandName}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = useAccent();
  const t = f / fps;
  const endAt = sc.endAt || sc.dur;
  const recap = interpolate(t - endAt, [0, 0.6], [1, 0], clamp);
  const es = interpolate(t - endAt, [0.2, 1], [0, 1], clamp);
  const pulse = 1 + 0.03 * Math.sin(f / 6);
  return (
    <AbsoluteFill>
      <Backdrop />
      <AbsoluteFill style={{padding: '150px 140px', flexDirection: 'column', gap: 32, opacity: recap}}>
        <div><Chip text="TÓM LẠI" /></div>
        {(sc.points || []).map((p, i) => {
          const s = interpolate(f - 10 - i * 12, [0, 14], [0, 1], clamp);
          return <div key={i} style={{display: 'flex', gap: 24, alignItems: 'baseline', opacity: s, transform: `translateX(${(1 - s) * -40}px)`,
            fontFamily: HEAD, fontWeight: 700, fontSize: 48, color: C.ink}}>
            <span style={{fontFamily: DISPLAY, color: ac}}>{String(i + 1).padStart(2, '0')}</span>{p}</div>;
        })}
      </AbsoluteFill>
      {t >= endAt ? (
        <AbsoluteFill style={{opacity: es}}>
          <div style={{position: 'absolute', left: 120, top: 120, display: 'flex', alignItems: 'center', gap: 22}}>
            <Img src={staticFile('logo.png')} style={{width: 110, height: 110, borderRadius: '50%'}} />
            <div>
              <div style={{fontFamily: HEAD, fontWeight: 700, fontSize: 52, color: C.ink}}>{brandName}</div>
              <div style={{fontFamily: FONT, fontSize: 28, color: C.muted}}>Insight crypto dễ hiểu, mỗi tuần</div>
            </div>
          </div>
          {[0, 1].map((k) => <div key={k} style={{position: 'absolute', top: 360, left: 120 + k * 860, width: 800, height: 450, borderRadius: 24,
            border: `2px dashed ${C.line}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: HEAD,
            color: C.muted, fontSize: 30}}>{k ? 'Video đề xuất' : 'Xem tiếp video này'}</div>)}
          <div style={{position: 'absolute', left: 120, bottom: 140, transform: `scale(${pulse})`, transformOrigin: 'left center',
            padding: '20px 44px', borderRadius: 99, background: C.red, color: '#fff', fontFamily: HEAD, fontWeight: 700, fontSize: 36}}>ĐĂNG KÝ KÊNH</div>
        </AbsoluteFill>
      ) : null}
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
      <Handle size={22} style={{position: 'absolute', right: 40, bottom: 24}} />
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
          <AccentCtx.Provider value={sc.project?.color || DEFAULT_ACCENT}>
            {sc.type === 'hook' ? <HookScene sc={sc} brand={brandName} source={props.post ? '@' + props.post.handle : undefined} /> : null}
            {sc.type === 'intro' ? <IntroScene sc={sc} post={props.post} brand={brandName} /> : null}
            {sc.type === 'section' ? <SectionScene sc={sc} data={props.data} brandName={brandName} post={props.post} /> : null}
            {sc.type === 'outro' ? <OutroScene sc={sc} brandName={brandName} /> : null}
            {sc.type !== 'hook' ? <Captions words={sc.words} bottom={64} size={40} maxWidth={1500} /> : null}
            {i > 0 ? <Glitch /> : null}
          </AccentCtx.Provider>
        </Sequence>
      ))}
      <AccentCtx.Provider value={cur?.project?.color || DEFAULT_ACCENT}><Chrome /></AccentCtx.Provider>
    </AbsoluteFill>
  );
};
