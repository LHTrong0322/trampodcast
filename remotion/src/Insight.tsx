import React from 'react';
import {AbsoluteFill, Audio, Img, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {HookImpact} from './HookImpact';
import {AccentCtx, tone, Backdrop, C, Captions, Chip, clamp, CountUp, FONT, Glitch, RevealWords, useAccent, useFonts, useSpring, Word} from './ui';
import {DataPanel, DataSpec} from './data';
import {Beat, BeatPanel} from './beats';

export type Post = {author: string; handle: string; avatar?: string; cover?: string; title?: string; text?: string;
  likes?: number; views?: number; retweets?: number};
export type Project = {name?: string; ticker?: string; logo?: string | null; color?: string | null};
export type Scene = {
  type: 'hook' | 'intro' | 'section' | 'outro';
  from: number; dur: number; words: Word[];
  hook?: string; stat?: string; label?: string; images?: string[];
  title?: string; theme?: string;
  idx?: number; total?: number; heading?: string; keyStat?: string; keyLabel?: string; bullets?: string[];
  quote?: string; source?: string; data?: DataSpec | null; beats?: Beat[]; points?: string[]; agendaLabel?: string; cta?: string; hidePost?: boolean; emphasis?: string; project?: Project | null;
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
  if ((sc as any).impact) return <HookImpact {...(sc as any).impact} />;   // Trọng 23/11: mở đầu kiểu cú sốc
  const zoom = 1 + Math.min(f, 600) * 0.00012;   // zoom chậm cho có chuyển động (review 1518)
  return (
  <AbsoluteFill>
    <Backdrop img={sc.images?.[0]} dim={0.7} />
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 26, transform: `scale(${zoom})`}}>
      {sc.beats?.length ? <div style={{order: 2}}><BeatPanel beats={sc.beats} t={f / 30} sceneDur={sc.dur} data={null} w={1100} h={470} /></div>
        : sc.stat ? <CountUp value={sc.stat} size={220} delay={4} /> : null}
      {sc.label && !sc.beats?.length ? <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 36, color: C.muted, letterSpacing: 4, textTransform: 'uppercase'}}>{sc.label}</div> : null}
      <div style={{maxWidth: 1500, textAlign: 'center', display: 'flex', justifyContent: 'center'}}>
        <RevealWords text={sc.hook || ''} size={sc.beats?.length ? 64 : sc.stat ? 66 : 96} delay={sc.stat ? 16 : 2} stagger={2} maxWidth={1560} />
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

// ---------- INTRO (Trọng 22/11: "phần mở đầu quá xấu và quá chán, đập đi xây lại") ----------
// Màn 1: tên kênh bật lên, tiêu đề tập lớn giữa màn, con số gây sốc làm nền chìm phía sau, thẻ so sánh/ nguồn nhỏ gọn.
// Màn 2: tiêu đề thu nhỏ lên góc trái, các chương trượt vào thành hàng thẻ số lớn, sáng lần lượt theo thời gian.
const IntroScene: React.FC<{sc: Scene; post: Post | null; data?: any}> = ({sc, post, data}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = useAccent();
  const t = f / fps;
  const pts = (sc.points || []).slice(0, 5);
  const agendaAt = Math.min(5.5, sc.dur * 0.38);
  const k = interpolate(t - agendaAt, [0, 0.7], [0, 1], {...clamp, easing: (x: number) => 1 - Math.pow(1 - x, 3)});
  const pop = useSpring(2, 14);
  const water = (sc as any).stat || '';
  const words = (sc.title || '').split(/\s+/).filter(Boolean);
  const cardW = Math.min(330, (1700 - (pts.length - 1) * 22) / Math.max(1, pts.length));
  const per = Math.max(0.5, (sc.dur - agendaAt - 0.8) / Math.max(1, pts.length));
  return (
    <AbsoluteFill style={{background: C.bg, overflow: 'hidden'}}>
      <Backdrop img={sc.images?.[0]} dim={0.92} />
      {/* con số gây sốc: màn 1 là khối số lớn bên phải, màn 2 chìm thành nền */}
      {water ? <div style={{position: 'absolute', right: interpolate(k, [0, 1], [110, -40]), top: interpolate(k, [0, 1], [360, 640]),
        fontFamily: FONT, fontWeight: 900, fontSize: interpolate(k, [0, 1], [210, 420]), letterSpacing: -6, lineHeight: 1, whiteSpace: 'nowrap',
        color: k > 0.5 ? `${ac}12` : (/^[-−]/.test(water) ? '#E5383B' : /^[+]/.test(water) ? '#1F9D63' : ac),
        opacity: interpolate(t, [1.0, 1.4], [0, 1], clamp), transform: `scale(${interpolate(t, [1.0, 1.5], [1.25, 1], clamp)})`, transformOrigin: 'right top'}}>
        {water}
        {(sc as any).statLabel && k < 0.5 ? <div style={{fontSize: 40, letterSpacing: 4, fontWeight: 800, color: C.muted, textAlign: 'right', marginTop: 12}}>
          {(sc as any).statLabel}</div> : null}
      </div> : null}
      {/* vệt màu chạy ngang khi chuyển cảnh */}
      <div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: `${interpolate(t - agendaAt, [-0.2, 0.35, 0.8], [0, 100, 0], clamp)}%`,
        background: `${ac}14`}} />
      {/* thanh thương hiệu */}
      <div style={{position: 'absolute', left: 110, top: 70, display: 'flex', alignItems: 'center', gap: 18, opacity: pop,
        transform: `translateY(${(1 - pop) * -30}px)`}}>
        <Img src={staticFile('logo.png')} style={{width: 84, height: 84, borderRadius: 999, boxShadow: `0 0 0 5px ${ac}33, 0 12px 30px rgba(40,50,110,0.18)`}} />
        <div>
          <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 32, letterSpacing: 4, color: C.ink}}>SMART PENGUIN INSIGHTS</div>
          <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 22, color: C.muted, letterSpacing: 1}}>@Trong0322 · {(sc.theme || 'Insight crypto').toUpperCase()}</div>
        </div>
      </div>
      {/* tiêu đề tập: lớn giữa màn → thu nhỏ lên trái */}
      <div style={{position: 'absolute', left: 110, width: water || (sc.hidePost && sc.beats?.length) ? 980 : 1700, top: interpolate(k, [0, 1], [330, 200]),
        display: 'flex', flexWrap: 'wrap', columnGap: 24, rowGap: 4, transformOrigin: 'left top',
        opacity: 1 - interpolate(k, [0, 0.6], [0, 1], clamp),
        transform: `scale(${interpolate(k, [0, 1], [1, 0.8])})`}}>
        {words.map((w, i) => {
          const s = interpolate(t - 0.35 - i * 0.07, [0, 0.35], [0, 1], clamp);
          const key = w.toLowerCase().replace(/[^\p{L}\p{N}$%]/gu, '');
          const hot = ((sc as any).hl || []).includes(key);
          return <span key={i} style={{fontFamily: FONT, fontWeight: 900, fontSize: 112, lineHeight: 1.28, paddingTop: 10, color: hot ? ac : C.ink,
            opacity: s, transform: `translateY(${(1 - s) * 40}px)`, display: 'inline-block'}}>{w}</span>;
        })}
        <div style={{flexBasis: '100%', height: 10, marginTop: 10, borderRadius: 99, background: ac, maxWidth: interpolate(t, [0.6, 1.6], [0, 420], clamp)}} />
      </div>
      {/* màn 2: tiêu đề gọn 1 đến 2 dòng, rộng hết màn (lỗi 23/11: tiêu đề dài thu nhỏ vẫn 4 dòng, đè nhãn chương) */}
      {k > 0 ? <div style={{position: 'absolute', left: 110, right: 110, top: 200, opacity: interpolate(k, [0.4, 1], [0, 1], clamp),
        fontFamily: FONT, fontWeight: 900, fontSize: words.join(' ').length > 60 ? 50 : 60, lineHeight: 1.2, color: C.ink,
        transform: `translateY(${interpolate(k, [0.4, 1], [24, 0], clamp)}px)`}}>{words.join(' ')}</div> : null}
      {/* thẻ so sánh (kịch bản của Trọng) hoặc nguồn nhỏ gọn, chỉ ở màn 1 */}
      {k < 1 && sc.hidePost && sc.beats?.length ? <div style={{position: 'absolute', right: 110, bottom: 190, opacity: interpolate(t, [1.2, 1.7], [0, 1], clamp) * (1 - k),
        transform: `scale(${0.8 + 0.2 * interpolate(t, [1.2, 1.7], [0, 1], clamp)})`, transformOrigin: 'right bottom'}}>
        <BeatPanel beats={sc.beats.slice(0, 1)} t={Math.max(2, t)} sceneDur={sc.dur} data={data} w={760} h={330} /></div> : null}
      {k < 1 && post && !sc.hidePost ? <div style={{position: 'absolute', right: 110, top: 64, display: 'flex', alignItems: 'center', gap: 14, opacity: (1 - k) * pop,
        padding: '12px 22px', borderRadius: 99, background: '#FFFFFF', border: `1px solid ${C.line}`, boxShadow: '0 10px 26px rgba(40,50,110,0.1)'}}>
        {post.avatar ? <Img src={staticFile(post.avatar)} style={{width: 44, height: 44, borderRadius: 99}} /> : null}
        <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 24, color: C.muted}}>Ý tưởng từ <b style={{color: C.ink}}>@{post.handle}</b> trên 𝕏</div>
      </div> : null}
      {/* màn 2: hàng thẻ chương */}
      {k > 0 ? <div style={{position: 'absolute', left: 110, right: 110, top: 470, display: 'flex', gap: 22}}>
        {pts.map((p, i) => {
          const s = interpolate(t - agendaAt - 0.25 - i * 0.12, [0, 0.45], [0, 1], {...clamp, easing: (x: number) => 1 - Math.pow(1 - x, 3)});
          const on = t >= agendaAt + 0.6 + i * per;
          return <div key={i} style={{width: cardW, minHeight: 300, padding: '26px 26px', borderRadius: 26, background: '#FFFFFF',
            border: `2px solid ${on ? ac : C.line}`, boxShadow: on ? `0 18px 44px ${ac}33` : '0 10px 28px rgba(40,50,110,0.10)',
            opacity: s, transform: `translateY(${(1 - s) * 120}px) scale(${on ? 1.03 : 1})`, display: 'flex', flexDirection: 'column', gap: 16}}>
            <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 76, lineHeight: 1, color: on ? ac : `${ac}66`}}>{String(i + 1).padStart(2, '0')}</div>
            <div style={{fontFamily: FONT, fontWeight: 800, fontSize: pts.length > 4 ? 30 : 34, lineHeight: 1.25, color: C.ink}}>{p}</div>
          </div>;
        })}
      </div> : null}
      {k > 0 && sc.agendaLabel ? <div style={{position: 'absolute', left: 110, top: 410, opacity: k}}><Chip text={sc.agendaLabel} /></div> : null}
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
          <div key={i} style={{display: 'flex', alignItems: 'center', gap: 18, opacity: s * (active ? 1 : 0.8),
            transform: `translateX(${(1 - s) * -40}px) scale(${active ? 1.03 : 1})`, transformOrigin: 'left center',
            padding: '8px 16px', marginLeft: -16, borderRadius: 14, background: active ? `${ac}18` : 'transparent',
            fontFamily: FONT, fontSize: 40, fontWeight: active ? 800 : 700, color: C.ink}}>
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

const SectionScene: React.FC<{sc: Scene; data: any; brandName: string; post?: Post | null}> = (p) => (
  // Trọng 22/11 (review: "câu số 4 đã hứa mà trình bày y hệt câu 1-3"): phần được nhấn đổi màu cam + nhãn riêng
  // Trọng 22/11: nền luôn sạch, phần nhấn chỉ đổi màu nhấn + nhãn, không tô nền
  p.sc.emphasis ? <AccentCtx.Provider value="#E8590C"><SectionInner {...p} /></AccentCtx.Provider> : <SectionInner {...p} />
);
const SectionInner: React.FC<{sc: Scene; data: any; brandName: string; post?: Post | null}> = ({sc, data, brandName, post}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = useAccent();
  const t = f / fps;
  const numS = useSpring(0, 20);
  const hasData = !!(sc.data && sc.data.type && sc.data.type !== 'none');
  const quoteAt = sc.dur * 0.55;
  const toQuote = hasData && !!sc.quote;
  // Trọng 22/11 (review: "khung nào cũng chữ trái + thẻ phải"): hình so sánh/biểu đồ chiếm trọn khung, cột chữ lùi đi
  const curBeat = [...(sc.beats || [])].sort((a, b) => a.s - b.s).filter((b) => t >= b.s - 0.15).pop();
  const wide = !!curBeat && ['race', 'versus', 'chart', 'wma'].includes(curBeat.type);
  const wideK = interpolate(t - (curBeat?.s ?? 0), [-0.15, 0.35], [0, 1], clamp) * (wide ? 1 : 0);
  return (
    <AbsoluteFill>
      <Backdrop />
      <TopBar source={sc.source} idx={sc.idx} total={sc.total} brand={brandName} project={sc.project} />
      <div style={{position: 'absolute', left: 110, top: 170, display: 'flex', alignItems: 'center', gap: 16, opacity: numS * (1 - wideK), fontFamily: FONT}}>
        <div style={{fontWeight: 800, fontSize: 30, color: ac}}>{String(sc.idx).padStart(2, '0')}</div>
        <div style={{width: 10, height: 10, borderRadius: 99, background: ac, transform: `scale(${numS})`}} />
        <div style={{color: C.muted, fontWeight: 700, fontSize: 22, letterSpacing: 4}}>INSIGHT</div>
      </div>
      <div style={{position: 'absolute', left: 110, top: 230, width: 800, display: 'flex', flexDirection: 'column', gap: 40, opacity: 1 - wideK}}>
        {sc.emphasis ? <div><Chip text={sc.emphasis} /></div> : null}
        <RevealWords text={sc.heading || ''} size={58} delay={1} stagger={1} maxWidth={800}
          highlight={[sc.project?.name || '', sc.keyStat || ''].filter(Boolean)} />
        {sc.bullets?.length ? <Bullets items={sc.bullets} dur={sc.dur} fps={fps} /> : null}
      </div>
      {wide ? <div style={{position: 'absolute', left: 140, top: 150, opacity: wideK, fontFamily: FONT, fontWeight: 800, fontSize: 30, color: ac}}>
        {String(sc.idx).padStart(2, '0')} · {(sc.heading || '').toUpperCase()}</div> : null}
      <div style={{position: 'absolute', right: wide ? 140 : 100, top: wide ? 210 : 190, width: wide ? 1640 : 840, height: wide ? 640 : 560,
        transform: wide ? 'none' : `scale(${1 + Math.min(t, 40) * 0.0015}) translateY(${-Math.min(t, 40) * 0.4}px)`, transformOrigin: 'center'}}>
        {sc.beats?.length ? <BeatPanel beats={sc.beats} t={t} sceneDur={sc.dur} data={data} w={wide ? 1640 : 840} h={wide ? 640 : 560} /> : null}
        {sc.beats?.length ? null : <>
        <div style={{position: 'absolute', inset: 0, opacity: toQuote ? interpolate(t - quoteAt, [0, 0.5], [1, 0], clamp) : 1}}>
          {hasData ? <DataPanel spec={sc.data!} data={data} w={840} h={560} />
            : <QuoteCard post={post || null} quote={sc.quote || sc.heading || ''} w={840} h={560} />}
        </div>
        {toQuote && t >= quoteAt ? (
          <div style={{position: 'absolute', inset: 0}}>
            <Sequence from={Math.round(quoteAt * fps)} layout="none"><QuoteCard post={post || null} quote={sc.quote!} w={840} h={560} /></Sequence>
          </div>
        ) : null}
        </>}
        {sc.keyStat && !sc.beats?.length ? (
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
          // review 2219: hiện đậm từng câu kèm dấu tick, rải đều theo lời đọc
          const n = (sc.points || []).length;
          const at = Math.round(fps * (0.6 + (Math.max(3, sc.dur * 0.3) * i) / Math.max(1, n)));   // review 22/11: hiện đủ các ý sớm
          const s = interpolate(f - at, [0, 12], [0, 1], clamp);
          return <div key={i} style={{display: 'flex', gap: 26, alignItems: 'center', opacity: s, transform: `translateX(${(1 - s) * -40}px)`,
            fontFamily: FONT, fontWeight: 800, fontSize: 58, color: C.ink}}>
            <div style={{width: 64, height: 64, borderRadius: 18, background: C.green, color: '#fff', fontSize: 40, display: 'flex',
              alignItems: 'center', justifyContent: 'center', transform: `scale(${s})`}}>✓</div>{p}</div>;
        })}
        {sc.cta ? <div style={{marginTop: 30, alignSelf: 'flex-start', padding: '18px 34px', borderRadius: 20, background: `${ac}14`, border: `2px solid ${ac}`,
          fontFamily: FONT, fontWeight: 800, fontSize: 52, color: ac,
          opacity: interpolate(f - Math.round(fps * Math.max(2, sc.dur * 0.35)), [0, 14], [0, 1], clamp)}}>{sc.cta}</div> : null}
      </AbsoluteFill>
      <div style={{position: 'absolute', right: 140, top: 140, opacity: btn, transform: `scale(${btn * pulse})`, fontFamily: FONT,
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
            {sc.type === 'intro' ? <IntroScene sc={sc} post={props.post} data={props.data} /> : null}
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
