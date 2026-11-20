import React from 'react';
import {AbsoluteFill, Audio, Img, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {AccentCtx, applyTheme, deepClean, EmphText, fitSize, tone, Backdrop, BRAND, glass, Handle, T, C, Captions, Chip, clamp, CountUp, DISPLAY, FONT, Glitch, HEAD, RevealWords, useAccent, useFonts, useSpring, Word} from './ui';
import {DataPanel, DataSpec, dataOk} from './data';

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
  endAt?: number; emph?: string[]; openLoop?: string; actions?: string[]; question?: string; cuts?: number[]; subs?: {t: string; s: number; e: number}[] | null; xquotes?: {text: string; vi?: string}[]; terms?: {term: string; explain: string; at: number}[];
};
export type InsightProps = {fps: number; width: number; height: number; audio: string; music?: string; duration: number;
  scenes: Scene[]; post: Post | null; brand: Record<string, string>; data?: any; logo?: string; mode?: string; shortTitle?: string;
  theme?: string; emph?: string[]; shortHook?: string};

export const accentDefault = () => BRAND.blue;
const fmt = (n?: number) => (n == null ? '' : n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : n >= 1e3 ? (n / 1e3).toFixed(1) + 'K' : String(n));

// ---------- thanh trên: logo kênh + nguồn ----------
const TopBar: React.FC<{source?: string; idx?: number; total?: number; brand: string; project?: Project | null}> = ({source, idx, total, brand, project}) => {
  const ac = useAccent();
  // logo + "SMART PENGUIN INSIGHTS" + Source hiện rõ ngay từ khung hình đầu tiên (không hiệu ứng mờ dần)
  return (
    <div style={{position: 'absolute', top: 44, left: 80, right: 80, display: 'flex', alignItems: 'center', gap: 18, fontFamily: FONT}}>
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
            background: i + 1 <= (idx || 0) ? ac : T.dim}} />)}
          <div style={{color: C.ink, fontFamily: DISPLAY, fontWeight: 800, fontSize: 22, marginLeft: 10}}>{String(idx).padStart(2, '0')}<span style={{color: C.muted}}>/{String(total).padStart(2, '0')}</span></div>
        </div>
      ) : null}
    </div>
  );
};

// ---------- chữ tiêu đề: hiện CẢ CÂU cùng lúc (mờ → rõ trong ~0,3s), không gõ từng chữ ----------
export const FadeText: React.FC<{text: string; size: number; maxWidth?: number; highlight?: string[]; color?: string}> = ({text, size, maxWidth, highlight = [], color}) => {
  const f = useCurrentFrame();
  const ac = useAccent();
  const o = interpolate(f, [0, 8], [0, 1], clamp);
  return <div style={{maxWidth, fontFamily: HEAD, fontWeight: 700, fontSize: size, lineHeight: 1.14, letterSpacing: -0.5, color: color || C.ink,
    opacity: o, transform: `translateY(${(1 - o) * 14}px)`, textShadow: T.textShadow}}>
    {text.split(/(\s+)/).map((w, i) => highlight.some((h) => h && w.toLowerCase().includes(h.toLowerCase())) ? <span key={i} style={{color: ac}}>{w}</span> : w)}
  </div>;
};

// ---------- HOOK: chữ hiện ĐỦ ngay giây 0 (không hiệu ứng gõ), cỡ lớn nhất khung, MỘT con số tô màu ----------
export const splitHook = (t: string) => {
  const parts = (t || '').split(/(?<=[.!?…])\s+/).filter(Boolean);
  return {main: parts[0] || '', rest: parts.slice(1).join(' ')};
};
export const StatText: React.FC<{text: string; stat?: string; size: number; color?: string; weight?: number; align?: 'center' | 'left'}> = ({text, stat, size, color, weight = 700, align = 'center'}) => {
  const ac = useAccent();
  const key = (stat || '').replace(/[^\d.,%$xKMBT]/g, '');
  return <div style={{fontFamily: HEAD, fontWeight: weight, fontSize: size, lineHeight: 1.14, color: color || C.ink, textAlign: align,
    letterSpacing: -0.5, textShadow: T.textShadow}}>
    {text.split(/(\s+)/).map((w, i) => (key && w.includes(key)) ? <span key={i} style={{color: ac, fontFamily: DISPLAY, fontWeight: 800}}>{w}</span> : w)}
  </div>;
};

const HookScene: React.FC<{sc: Scene; brand: string; source?: string}> = ({sc, brand, source}) => {
  const f = useCurrentFrame();
  const {main, rest} = splitHook(sc.hook || '');
  const size = fitSize(main, 1560, rest ? 400 : 560, 124, 72);
  const ring = (k: number) => ((f + k * 18) % 54) / 54;
  return (
  <AbsoluteFill>
    <Backdrop img={sc.images?.[0]} dim={0.75} />
    <TopBar brand={brand} source={source} />
    {[0, 1, 2].map((k) => <div key={k} style={{position: 'absolute', left: '50%', top: '52%', width: 1100, height: 1100,
      marginLeft: -550, marginTop: -550, borderRadius: '50%', border: `2px solid ${C.line}`,
      transform: `scale(${0.3 + ring(k) * 1.2})`, opacity: (1 - ring(k)) * 0.14}} />)}
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 34, padding: '150px 160px 60px'}}>
      {sc.stat && sc.label ? <Chip text={`${sc.stat} · ${sc.label}`.toUpperCase()} size={30} /> : null}
      <div style={{maxWidth: 1600, transform: `scale(${1 + 0.015 * Math.min(1, f / 90)})`}}>
        <StatText text={main} stat={sc.stat} size={size} />
      </div>
      {rest ? <div style={{maxWidth: 1400}}><StatText text={rest} size={Math.min(58, Math.round(size * 0.55))} color={C.muted} weight={500} /></div> : null}
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

// ---------- INTRO: rất ngắn, tiêu đề + VÒNG LẶP MỞ (điều sẽ có ở cuối video), không còn mục lục dài ----------
const IntroScene: React.FC<{sc: Scene; post: Post | null; brand: string}> = ({sc, post, brand}) => {
  const ac = useAccent();
  const ol = useSpring(10, 16);
  return (
    <AbsoluteFill>
      <Backdrop img={sc.images?.[0]} dim={0.88} />
      <TopBar brand={brand} source={post ? '@' + post.handle : undefined} />
      <AbsoluteFill style={{flexDirection: 'row', alignItems: 'center', padding: '60px 110px 120px', gap: 70}}>
        <div style={{flex: 1, display: 'flex', flexDirection: 'column', gap: 30}}>
          <div><Chip text={(sc.theme || 'INSIGHT').toUpperCase()} /></div>
          <FadeText text={sc.title || ''} size={fitSize(sc.title || '', 900, 260, 66, 44)} maxWidth={900} />
          {sc.openLoop ? (
            <div style={{display: 'flex', alignItems: 'center', gap: 22, padding: '24px 30px', borderRadius: 22, ...glass,
              borderLeft: `6px solid ${ac}`, opacity: ol, transform: `translateY(${(1 - ol) * 24}px)`, maxWidth: 900}}>
              <div style={{fontSize: 46}}>🎯</div>
              <div style={{fontFamily: HEAD, fontWeight: 700, fontSize: fitSize(sc.openLoop, 760, 130, 42, 30), color: C.ink, lineHeight: 1.25}}>{sc.openLoop}</div>
            </div>
          ) : null}
        </div>
        {post ? <PostCard post={post} delay={4} /> : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------- SECTION (kiểu "dữ liệu thật") ----------
const Bullets: React.FC<{items: string[]; dur: number; fps: number; emph?: string[]}> = ({items, dur, fps, emph}) => {
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
            <span><EmphText text={b} emph={emph} weight={700} /></span>
          </div>
        );
      })}
    </div>
  );
};

export const QuoteCard: React.FC<{post: Post | null; quote: string; w: number; h: number; emph?: string[]}> = ({post, quote, w, h, emph}) => {
  const s = useSpring(2, 18);
  const ac = useAccent();
  return (
    <div style={{width: w, height: h, borderRadius: 26, ...glass, boxSizing: 'border-box',
      padding: 50, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 26, fontFamily: FONT, opacity: s,
      transform: `scale(${0.96 + 0.04 * s})`, boxShadow: '0 30px 80px rgba(0,0,0,0.4)', borderLeft: `6px solid ${ac}`}}>
      <div style={{fontFamily: HEAD, fontSize: 44, lineHeight: 1.28, color: C.ink, fontWeight: 500}}>“<EmphText text={quote} emph={emph} color={ac} weight={700} />”</div>
      {post ? <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
        {post.avatar ? <Img src={staticFile(post.avatar)} style={{width: 52, height: 52, borderRadius: '50%'}} /> : null}
        <div style={{color: C.muted, fontSize: 24, fontWeight: 500}}>Source: <b style={{color: C.ink}}>@{post.handle}</b></div>
      </div> : null}
    </div>
  );
};

// thẻ trích nguyên văn câu highlight của tác giả trên X (kèm dịch)
const XQuoteCard: React.FC<{post: Post | null; text: string; vi?: string; w: number; h: number; emph?: string[]}> = ({post, text, vi, w, h, emph}) => {
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
      <div style={{fontFamily: HEAD, color: C.ink, fontSize: (vi || text).length > 130 ? 36 : 42, fontWeight: 500, lineHeight: 1.3}}>“<EmphText text={vi || text} emph={emph} color={ac} weight={700} />”</div>
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
      transform: `translateY(${(1 - o) * 16}px)`, padding: '14px 22px', borderRadius: 16, background: C.panel,
      border: `1px solid ${C.line}`, maxWidth: 820, fontFamily: FONT}}>
      <div style={{fontSize: 30}}>💡</div>
      <div style={{color: C.ink, fontSize: 25, lineHeight: 1.3}}><b style={{fontFamily: HEAD, color: ac}}>{cur.term}</b>: {cur.explain}</div>
    </div>
  );
};

// ---------- "nhịp hình": mỗi 5-8 giây (đổi ở cuối câu) đổi 1 cảnh: dữ liệu, số lớn, ảnh Ken Burns, thuật ngữ, logo, trích X ----------
type Beat = {kind: 'data' | 'stat' | 'image' | 'x' | 'quote' | 'term' | 'project'; text?: string; vi?: string; img?: string; term?: string; explain?: string};

export const buildBeats = (sc: Scene, data: any): Beat[] => {
  const b: Beat[] = [];
  const add = (x: Beat | null) => { if (x) b.push(x); };
  add(dataOk(sc.data, data) ? {kind: 'data'} : null);
  add(sc.keyStat ? {kind: 'stat'} : null);
  add(sc.images?.[0] ? {kind: 'image', img: sc.images[0]} : null);
  const q = (sc.xquotes || [])[0];   // tối đa 1 thẻ trích X mỗi phần
  add(q ? {kind: 'x', text: q.text, vi: q.vi} : null);
  add(sc.terms?.[0] ? {kind: 'term', term: sc.terms[0].term, explain: sc.terms[0].explain} : null);
  add(sc.project?.logo ? {kind: 'project'} : null);
  add(sc.images?.[1] ? {kind: 'image', img: sc.images[1]} : null);
  add(!q && sc.quote ? {kind: 'quote', text: sc.quote} : null);
  if (!b.length) b.push({kind: 'quote', text: sc.quote || sc.heading});
  return b;
};

const BigStat: React.FC<{sc: Scene; w: number; h: number}> = ({sc, w, h}) => {
  const ac = useAccent();
  return <div style={{width: w, height: h, borderRadius: 26, ...glass, boxSizing: 'border-box', padding: 50, display: 'flex',
    flexDirection: 'column', justifyContent: 'center', gap: 22, borderTop: `4px solid ${ac}`}}>
    <div style={{fontFamily: HEAD, color: C.muted, fontWeight: 700, fontSize: 24, letterSpacing: 3}}>CON SỐ ĐÁNG CHÚ Ý</div>
    <CountUp value={sc.keyStat || ''} size={Math.min(190, Math.round((w - 100) / Math.max(3, (sc.keyStat || '').length) * 1.5))} delay={4} color={ac} />
    <div style={{fontFamily: HEAD, color: C.ink, fontWeight: 700, fontSize: fitSize(sc.keyLabel || '', w - 100, 130, 44, 28), lineHeight: 1.2}}>{sc.keyLabel}</div>
    {sc.source ? <div style={{color: C.muted, fontSize: 22, fontFamily: FONT}}>Source: <b style={{color: C.ink}}>{sc.source}</b></div> : null}
  </div>;
};

const KenBurns: React.FC<{img: string; w: number; h: number; t: number; per: number; dir: number}> = ({img, w, h, t, per, dir}) => {
  const k = Math.min(1, Math.max(0, t / per));
  return <div style={{width: w, height: h, borderRadius: 26, overflow: 'hidden', position: 'relative', boxShadow: T.shadow, border: `1px solid ${C.line}`}}>
    <Img src={staticFile(img)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover',
      transform: `scale(${1.06 + 0.12 * k}) translateX(${dir * 24 * k}px)`}} />
  </div>;
};

const TermCard: React.FC<{term: string; explain: string; w: number; h: number}> = ({term, explain, w, h}) => {
  const ac = useAccent();
  return <div style={{width: w, height: h, borderRadius: 26, ...glass, boxSizing: 'border-box', padding: 54, display: 'flex',
    flexDirection: 'column', justifyContent: 'center', gap: 26, borderLeft: `6px solid ${ac}`}}>
    <div><Chip text="💡 THUẬT NGỮ" size={24} /></div>
    <div style={{fontFamily: DISPLAY, fontWeight: 800, fontSize: fitSize(term, w - 110, 160, 92, 48), color: ac, lineHeight: 1.1}}>{term}</div>
    <div style={{fontFamily: HEAD, fontWeight: 500, fontSize: fitSize(explain, w - 110, 170, 44, 28), color: C.ink, lineHeight: 1.3}}>{explain}</div>
  </div>;
};

const ProjectCard: React.FC<{p: Project; w: number; h: number}> = ({p, w, h}) => {
  const ac = useAccent();
  const f = useCurrentFrame();
  return <div style={{width: w, height: h, borderRadius: 26, ...glass, boxSizing: 'border-box', display: 'flex', flexDirection: 'column',
    alignItems: 'center', justifyContent: 'center', gap: 26}}>
    {p.logo ? <Img src={staticFile(p.logo)} style={{width: 230, height: 230, borderRadius: '50%', boxShadow: `0 0 0 ${10 + 3 * Math.sin(f / 10)}px ${ac}33`}} /> : null}
    <div style={{fontFamily: HEAD, fontWeight: 700, fontSize: 60, color: C.ink}}>{p.name}</div>
    {p.ticker ? <Chip text={'$' + p.ticker} size={30} /> : null}
  </div>;
};

export const BeatStage: React.FC<{sc: Scene; data: any; post: Post | null; w: number; h: number}> = ({sc, data, post, w, h}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  const beats = buildBeats(sc, data);
  const cuts = sc.cuts && sc.cuts.length ? sc.cuts : [0];
  const segs = cuts.map((c, j) => ({at: c, end: cuts[j + 1] ?? sc.dur}));
  const si = Math.max(0, segs.findIndex((g) => t >= g.at && t < g.end));
  return (
    <div style={{position: 'relative', width: w, height: h}}>
      {segs.map((g, j) => {
        if (Math.abs(j - si) > 1) return null;
        const b = beats[j % beats.length];
        const per = Math.max(1, g.end - g.at);
        const o = j === si ? (j === 0 ? 1 : interpolate(t - g.at, [0.12, 0.45], [0, 1], clamp)) : j === si - 1 ? interpolate(t - segs[si].at, [0, 0.18], [1, 0], clamp) : 0;
        if (o <= 0) return null;
        const zoom = b.kind === 'image' ? 1 : 1 + 0.03 * Math.min(1, (t - g.at) / per);   // zoom chậm kiểu Ken Burns
        return (
          <div key={j} style={{position: 'absolute', inset: 0, opacity: o, transform: `scale(${zoom}) translateX(${(1 - o) * (j === si ? 50 : -50)}px)`}}>
            <Sequence from={Math.round(g.at * fps)} layout="none">
              {b.kind === 'data' ? <DataPanel spec={sc.data!} data={data} w={w} h={h} />
                : b.kind === 'stat' ? <BigStat sc={sc} w={w} h={h} />
                  : b.kind === 'image' ? <KenBurns img={b.img!} w={w} h={h} t={t - g.at} per={per} dir={j % 2 ? -1 : 1} />
                    : b.kind === 'term' ? <TermCard term={b.term!} explain={b.explain!} w={w} h={h} />
                      : b.kind === 'project' ? <ProjectCard p={sc.project!} w={w} h={h} />
                        : b.kind === 'x' ? <XQuoteCard post={post} text={b.text!} vi={b.vi} w={w} h={h} emph={sc.emph} />
                          : <QuoteCard post={post} quote={b.text || ''} w={w} h={h} emph={sc.emph} />}
            </Sequence>
          </div>
        );
      })}
    </div>
  );
};

const SectionScene: React.FC<{sc: Scene; data: any; brandName: string; post?: Post | null}> = ({sc, data, brandName, post}) => {
  const {fps} = useVideoConfig();
  const ac = useAccent();
  const numS = useSpring(0, 20);
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
        <FadeText text={sc.heading || ''} size={fitSize(sc.heading || '', 800, 210, 58, 40)} maxWidth={800}
          highlight={[sc.project?.name || ''].filter(Boolean)} />
        {sc.bullets?.length ? <Bullets items={sc.bullets} dur={sc.dur} fps={fps} emph={sc.emph} /> : null}
      </div>
      {sc.terms?.length ? <TermCallout terms={sc.terms} /> : null}
      <div style={{position: 'absolute', right: 100, top: 190}}>
        <BeatStage sc={sc} data={data} post={post || null} w={840} h={560} />
      </div>
    </AbsoluteFill>
  );
};

// ---------- OUTRO: 3 tiêu chí làm ngay + 1 câu hỏi kéo bình luận → màn hình kết thúc (chừa chỗ gắn 2 video + nút đăng ký) ----------
const OutroScene: React.FC<{sc: Scene; brandName: string}> = ({sc, brandName}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = useAccent();
  const t = f / fps;
  const endAt = sc.endAt || sc.dur;
  const recap = interpolate(t - endAt, [0, 0.6], [1, 0], clamp);
  const es = interpolate(t - endAt, [0.2, 1], [0, 1], clamp);
  const pulse = 1 + 0.03 * Math.sin(f / 6);
  const acts = sc.actions && sc.actions.length ? sc.actions : null;
  const list = acts || sc.points || [];
  // tiêu chí hiện dần theo lúc được đọc (khoảng 60% đầu lời kết), câu hỏi hiện sau đó
  const step = (endAt * 0.6) / Math.max(1, list.length);
  const qAt = Math.min(endAt - 1.5, endAt * 0.62);
  const qs = interpolate(t - qAt, [0, 0.5], [0, 1], clamp);
  return (
    <AbsoluteFill>
      <Backdrop />
      <div style={{opacity: recap}}><TopBar brand={brandName} /></div>
      <AbsoluteFill style={{padding: '180px 140px 200px', flexDirection: 'column', justifyContent: 'center', gap: 34, opacity: recap}}>
        <div><Chip text={acts ? `${list.length} TIÊU CHÍ LÀM NGAY` : 'TÓM LẠI'} size={30} /></div>
        {list.map((p, i) => {
          const s = interpolate(t - 0.3 - i * step, [0, 0.4], [0, 1], clamp);
          return <div key={i} style={{display: 'flex', gap: 26, alignItems: 'center', opacity: 0.25 + 0.75 * s, transform: `translateX(${(1 - s) * -30}px)`,
            fontFamily: HEAD, fontWeight: 700, fontSize: acts ? 72 : 48, color: C.ink}}>
            {acts ? <div style={{width: 62, height: 62, borderRadius: 16, background: s > 0.5 ? ac : 'transparent', border: `3px solid ${ac}`,
              color: '#fff', fontSize: 40, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>{s > 0.5 ? '✓' : ''}</div>
              : <span style={{fontFamily: DISPLAY, color: ac}}>{String(i + 1).padStart(2, '0')}</span>}
            {p}</div>;
        })}
        {sc.question ? (
          <div style={{marginTop: 18, display: 'flex', alignItems: 'center', gap: 22, padding: '26px 34px', borderRadius: 22, ...glass,
            borderLeft: `6px solid ${ac}`, opacity: qs, transform: `translateY(${(1 - qs) * 24}px)`, maxWidth: 1500}}>
            <div style={{fontSize: 48}}>💬</div>
            <div style={{fontFamily: HEAD, fontWeight: 700, fontSize: 52, color: C.ink, lineHeight: 1.25}}>{sc.question}</div>
          </div>
        ) : null}
      </AbsoluteFill>
      {t >= endAt ? (
        <AbsoluteFill style={{opacity: es}}>
          <div style={{position: 'absolute', left: 120, top: 120, display: 'flex', alignItems: 'center', gap: 22}}>
            <Img src={staticFile('logo.png')} style={{width: 110, height: 110, borderRadius: '50%'}} />
            <div>
              <div style={{fontFamily: HEAD, fontWeight: 700, fontSize: 52, color: C.ink}}>{brandName}</div>
              <div style={{fontFamily: FONT, fontSize: 28, color: C.muted}}>{sc.question ? 'Trả lời câu hỏi ở phần bình luận nhé' : 'Insight crypto dễ hiểu, mỗi tuần'}</div>
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
      <Handle size={26} style={{position: 'absolute', right: 36, bottom: 18}} />
    </>
  );
};

export const Insight: React.FC<InsightProps> = (raw) => {
  const props = React.useMemo(() => deepClean(raw), [raw]);
  applyTheme(props.theme);
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
          <AccentCtx.Provider value={tone(sc.project?.color) || accentDefault()}>
            {sc.type === 'hook' ? <HookScene sc={sc} brand={brandName} source={props.post ? '@' + props.post.handle : undefined} /> : null}
            {sc.type === 'intro' ? <IntroScene sc={sc} post={props.post} brand={brandName} /> : null}
            {sc.type === 'section' ? <SectionScene sc={sc} data={props.data} brandName={brandName} post={props.post} /> : null}
            {sc.type === 'outro' ? <OutroScene sc={sc} brandName={brandName} /> : null}
            {sc.type !== 'hook' ? <Captions words={sc.words} bottom={64} size={40} maxWidth={1500} emph={sc.emph || props.emph} subs={sc.subs} /> : null}
            {i > 0 ? <Glitch /> : null}
          </AccentCtx.Provider>
        </Sequence>
      ))}
      <AccentCtx.Provider value={tone(cur?.project?.color) || accentDefault()}><Chrome /></AccentCtx.Provider>
    </AbsoluteFill>
  );
};
