import React from 'react';
import {Img, interpolate, staticFile, useCurrentFrame, useVideoConfig, spring} from 'remotion';
import {BRAND, T, C, clamp, DISPLAY, ease, FONT, glass, HEAD, useAccent} from './ui';

export type Chart = {ticker: string; series: number[]; days: number; start?: string; end?: string; recent?: boolean};
export type DataSpec = {type: string; tickers?: string[]; items?: {label: string; value?: string; num?: number}[]; title?: string; chart?: Chart | null};

const Frame: React.FC<{w: number; h: number; title: string; sub?: string; children: React.ReactNode}> = ({w, h, title, sub, children}) => {
  const ac = useAccent();
  return (
  <div style={{width: w, height: h, borderRadius: 26, ...glass, borderTop: `4px solid ${ac}`,
    boxShadow: T.shadow, padding: 36, boxSizing: 'border-box', fontFamily: FONT,
    display: 'flex', flexDirection: 'column', gap: 18, overflow: 'hidden'}}>
    <div style={{display: 'flex', alignItems: 'baseline', gap: 14}}>
      <div style={{color: C.ink, fontFamily: HEAD, fontWeight: 700, fontSize: 32, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: sub === '' ? w - 80 : w - 300}}>{title}</div>
      <div style={{flex: 1}} />
      {sub === '' ? null : <div style={{color: C.muted, fontWeight: 600, fontSize: 18, whiteSpace: 'nowrap'}}>{sub || 'Dữ liệu thật · CoinGecko'}</div>}
    </div>
    <div style={{flex: 1, position: 'relative'}}>{children}</div>
  </div>
  );
};

const useP = (delay = 0, len = 36) => {
  const f = useCurrentFrame();
  return interpolate(f - delay, [0, len], [0, 1], {...clamp, easing: ease});
};

const money = (v: number) => (v >= 1e12 ? `$${(v / 1e12).toFixed(2)}T` : v >= 1e9 ? `$${(v / 1e9).toFixed(1)}B` : v >= 1e6 ? `$${(v / 1e6).toFixed(1)}M`
  : v >= 1000 ? `$${Math.round(v).toLocaleString('en-US')}` : v >= 1 ? `$${v.toFixed(2)}` : `$${v.toPrecision(3)}`);

// ---- Fear & Greed gauge ----
const FearGreed: React.FC<{data: any; w: number; h: number}> = ({data, w, h}) => {
  const fg = data?.fear_greed || [];
  const now = fg[0]?.v ?? 50;
  const p = useP(4, 40);
  const v = now * p;
  const ang = -180 + (v / 100) * 180;
  const R = 210;
  const cx = (w - 72) / 2;
  const color = v < 25 ? C.red : v < 45 ? '#FF8A3D' : v < 55 ? C.gold : v < 75 ? '#9BE15D' : C.green;
  const arc = (a0: number, a1: number) => {
    const p0 = [cx + R * Math.cos((a0 * Math.PI) / 180), 280 + R * Math.sin((a0 * Math.PI) / 180)];
    const p1 = [cx + R * Math.cos((a1 * Math.PI) / 180), 280 + R * Math.sin((a1 * Math.PI) / 180)];
    return `M ${p0[0]} ${p0[1]} A ${R} ${R} 0 0 1 ${p1[0]} ${p1[1]}`;
  };
  const segs = [[C.red, -180, -135], ['#FF8A3D', -135, -99], [C.gold, -99, -81], ['#9BE15D', -81, -45], [C.green, -45, 0]];
  const week = fg[7]?.v, month = fg[29]?.v;
  return (
    <Frame w={w} h={h} title="Chỉ số Sợ hãi & Tham lam" sub="Dữ liệu thật · alternative.me">
      <svg width={w - 72} height={300} style={{position: 'absolute', top: -10}}>
        {segs.map(([c, a, b], i) => <path key={i} d={arc(a as number, b as number)} stroke={c as string} strokeWidth={34} fill="none" opacity={0.85} />)}
        <line x1={cx} y1={280} x2={cx + (R - 40) * Math.cos((ang * Math.PI) / 180)} y2={280 + (R - 40) * Math.sin((ang * Math.PI) / 180)}
          stroke="#fff" strokeWidth={10} strokeLinecap="round" />
        <circle cx={cx} cy={280} r={18} fill="#fff" />
      </svg>
      <div style={{position: 'absolute', left: 0, right: 0, top: 285, display: 'flex', justifyContent: 'center', alignItems: 'baseline', gap: 22}}>
        <div style={{fontSize: 84, fontWeight: 800, color, lineHeight: 1}}>{Math.round(v)}</div>
        <div style={{fontSize: 34, fontWeight: 800, color: C.ink}}>{fg[0]?.label || ''}</div>
      </div>
      <div style={{position: 'absolute', bottom: 0, left: 0, right: 0, display: 'flex', justifyContent: 'center', gap: 50, color: C.muted, fontSize: 24, fontWeight: 600}}>
        {week != null ? <span>7 ngày trước: <b style={{color: C.ink}}>{week}</b></span> : null}
        {month != null ? <span>30 ngày trước: <b style={{color: C.ink}}>{month}</b></span> : null}
      </div>
    </Frame>
  );
};

// ---- dominance donut ----
const Dominance: React.FC<{data: any; w: number; h: number}> = ({data, w, h}) => {
  const d = data?.global?.dominance || {};
  const btc = d.btc || 0, eth = d.eth || 0, st = (d.usdt || 0) + (d.usdc || 0);
  const other = Math.max(0, 100 - btc - eth - st);
  const parts = [['Bitcoin', btc, '#F7931A'], ['Ethereum', eth, '#8C8CFF'], ['Stablecoin', st, C.green], ['Altcoin khác', other, C.pink]] as const;
  const p = useP(4, 45);
  const R = 150, r = 2 * Math.PI * R;
  let acc = 0;
  return (
    <Frame w={w} h={h} title="Thị phần vốn hoá (Dominance)">
      <div style={{display: 'flex', alignItems: 'center', gap: 50, height: '100%'}}>
        <svg width={360} height={360} style={{transform: 'rotate(-90deg)'}}>
          {parts.map(([n, v, c], i) => {
            const len = (v / 100) * r * p;
            const el = <circle key={i} cx={180} cy={180} r={R} fill="none" stroke={c} strokeWidth={56}
              strokeDasharray={`${len} ${r}`} strokeDashoffset={-acc * p} />;
            acc += (v / 100) * r;
            return el;
          })}
        </svg>
        <div style={{display: 'flex', flexDirection: 'column', gap: 18}}>
          {parts.map(([n, v, c], i) => (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 16, opacity: interpolate(p, [i * 0.15, i * 0.15 + 0.3], [0, 1], clamp)}}>
              <div style={{width: 22, height: 22, borderRadius: 6, background: c}} />
              <div style={{color: C.ink, fontSize: 30, fontWeight: 700, width: 210}}>{n}</div>
              <div style={{color: c, fontSize: 40, fontWeight: 800}}>{(v * p).toFixed(1)}%</div>
            </div>
          ))}
          {data?.global?.mcap ? <div style={{color: C.muted, fontSize: 22, fontWeight: 600, marginTop: 8}}>Tổng vốn hoá: <b style={{color: C.ink}}>{money(data.global.mcap)}</b></div> : null}
        </div>
      </div>
    </Frame>
  );
};

// ---- heatmap of top coins ----
const Heatmap: React.FC<{data: any; w: number; h: number}> = ({data, w, h}) => {
  const f = useCurrentFrame();
  const mk = (data?.markets || []).filter((m: any) => !['USDT', 'USDC', 'DAI', 'USDE', 'FDUSD', 'USDS', 'PYUSD', 'USD1', 'BUIDL', 'USDTB', 'WBTC', 'STETH', 'WSTETH', 'WEETH', 'CBBTC', 'WETH', 'BSC-USD'].includes(m.sym)
    && /^[A-Z0-9]{2,5}$/.test(m.sym)).slice(0, 15);
  const cols = 5;
  const cw = Math.floor((w - 84 - (cols - 1) * 10) / cols);
  return (
    <Frame w={w} h={h} title="Top coin · 7 ngày">
      <div style={{display: 'flex', flexWrap: 'wrap', gap: 10}}>
        {mk.map((m: any, i: number) => {
          const c = m.chg7 ?? 0;
          const k = Math.min(1, Math.abs(c) / 15);
          const bg = c >= 0 ? `rgba(60,196,141,${0.12 + 0.38 * k})` : `rgba(229,103,125,${0.12 + 0.38 * k})`;
          const s = interpolate(f - i * 2, [0, 12], [0, 1], clamp);
          return (
            <div key={m.sym} style={{width: cw, height: 112, borderRadius: 16, background: bg, display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center', gap: 4, opacity: s, transform: `scale(${0.8 + 0.2 * s})`}}>
              <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
                <Img src={staticFile(`logos/${m.sym}.png`)} style={{width: 30, height: 30, borderRadius: 99}} />
                <span style={{color: T.tileInk, fontWeight: 800, fontSize: 26}}>{m.sym}</span>
              </div>
              <div style={{color: T.tileInk, fontWeight: 800, fontSize: 28}}>{c >= 0 ? '+' : ''}{c.toFixed(1)}%</div>
            </div>
          );
        })}
      </div>
    </Frame>
  );
};

// ---- coin chart ----
const CoinChart: React.FC<{data: any; spec: DataSpec; w: number; h: number}> = ({data, spec, w, h}) => {
  // biểu đồ đã kiểm tra khớp lời đọc (đúng khoảng thời gian sự kiện) do Python gắn vào spec.chart
  const ch = spec.chart;
  const sym = (ch?.ticker || spec.tickers?.[0] || 'BTC').replace('$', '').toUpperCase();
  const coin = data?.coins?.[sym];
  const mk = (data?.markets || []).find((x: any) => x.sym === sym);
  const series: number[] = ch?.series || coin?.series || (sym === 'BTC' && data?.btc_90d?.length ? data.btc_90d : mk?.spark || []);
  const m = {sym, name: coin?.name || mk?.name || sym, price: series[series.length - 1]};
  const days = ch ? ch.days : coin ? coin.days : sym === 'BTC' && data?.btc_90d ? 90 : 7;
  const period = ch?.start ? `${days} ngày (${ch.start} → ${ch.end})` : ch?.end ? `${days} ngày gần nhất, đến ${ch.end}` : `${days} ngày`;
  const p = useP(4, 50);
  const W = w - 72, H = h - 200;
  if (!series.length) return <Frame w={w} h={h} title={sym}><div /></Frame>;
  const lo = Math.min(...series), hi = Math.max(...series);
  const pts = series.map((v, i) => [(i / (series.length - 1)) * W, H - ((v - lo) / (hi - lo || 1)) * (H - 20) - 10]);
  const n = Math.max(2, Math.round(pts.length * p));
  const path = pts.slice(0, n).map((q, i) => `${i ? 'L' : 'M'}${q[0].toFixed(1)},${q[1].toFixed(1)}`).join(' ');
  const up = series[series.length - 1] >= series[0];
  const col = up ? C.green : C.red;
  const chg = ((series[series.length - 1] / series[0] - 1) * 100);
  const last = pts[n - 1];
  const f = useCurrentFrame();
  // điểm nhấn: đỉnh, đáy, mức giá đầu kỳ
  const iHi = series.indexOf(hi), iLo = series.indexOf(lo);
  const y0 = pts[0][1];
  const lab = (i: number, txt: string, c: string, above: boolean) => {
    if (i >= n) return null;
    const [x, y] = pts[i];
    const o = interpolate(f, [Math.round((i / pts.length) * 50) + 6, Math.round((i / pts.length) * 50) + 16], [0, 1], clamp);
    const lx = Math.min(W - 150, Math.max(0, x - 70));
    const ly = above ? Math.max(4, y - 52) : Math.min(H - 40, y + 16);   // không tràn lên dòng giá phía trên
    return <g key={txt} opacity={o}>
      <circle cx={x} cy={y} r={8} fill={c} stroke={T.solid} strokeWidth={3} />
      <rect x={lx} y={ly} width={150} height={36} rx={10} fill={T.solid} stroke={c} strokeWidth={1.5} />
      <text x={lx + 75} y={ly + 25} fill={C.ink} fontSize={20} fontFamily="HEAD" fontWeight={700} textAnchor="middle">{txt}</text>
    </g>;
  };
  const pulse = 10 + 6 * Math.abs(Math.sin(f / 8));
  return (
    <Frame w={w} h={h} title={`${m.name} · ${period}`} sub={ch?.start ? 'Giá thật · CoinGecko' : undefined}>
      <div style={{display: 'flex', alignItems: 'center', gap: 18, marginBottom: 10}}>
        <Img src={staticFile(`logos/${m?.sym || sym}.png`)} style={{width: 52, height: 52, borderRadius: '50%'}} />
        <div style={{color: C.ink, fontFamily: DISPLAY, fontSize: 44, fontWeight: 800}}>{money(m.price)}</div>
        <div style={{color: col, fontFamily: DISPLAY, fontSize: 32, fontWeight: 800}}>{chg >= 0 ? '+' : ''}{chg.toFixed(1)}%</div>
      </div>
      <svg width={W} height={H} style={{overflow: 'hidden'}}>
        <defs><linearGradient id="g" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor={col} stopOpacity={0.4} /><stop offset="1" stopColor={col} stopOpacity={0} /></linearGradient></defs>
        <line x1={0} x2={W} y1={y0} y2={y0} stroke={C.muted} strokeDasharray="6 8" strokeWidth={1.5} opacity={0.6} />
        <text x={W} y={y0 - 8} fill={C.muted} fontSize={18} textAnchor="end" fontFamily="BODY">đầu kỳ {money(series[0])}</text>
        <path d={`${path} L${last[0]},${H} L0,${H} Z`} fill="url(#g)" />
        <path d={path} stroke={col} strokeWidth={4} fill="none" strokeLinejoin="round" />
        {lab(iHi, `Đỉnh ${money(hi)}`, BRAND.orange, true)}
        {lab(iLo, `Đáy ${money(lo)}`, BRAND.sky, false)}
        <circle cx={last[0]} cy={last[1]} r={pulse} fill={col} opacity={0.25} />
        <circle cx={last[0]} cy={last[1]} r={8} fill={C.ink} />
      </svg>
    </Frame>
  );
};

// ---- stat compare bars: CHỈ khi mọi giá trị là số cùng đơn vị (Python đã tính sẵn num) ----
const StatCompare: React.FC<{spec: DataSpec; w: number; h: number}> = ({spec, w, h}) => {
  const items = (spec.items || []).slice(0, 4);
  const nums = items.map((it) => (typeof it.num === 'number' ? it.num : NaN));
  const p = useP(4, 40);
  const ac = useAccent();
  if (nums.some((n) => !isFinite(n)) || items.length < 2) return <TextCards spec={spec} w={w} h={h} />;
  const mx = Math.max(...nums) || 1;
  const cols = [ac, `${ac}CC`, `${ac}99`, `${ac}77`];
  return (
    <Frame w={w} h={h} title={spec.title || 'So sánh'} sub="Số liệu từ bài gốc">
      <div style={{display: 'flex', flexDirection: 'column', gap: 26, justifyContent: 'center', height: '100%'}}>
        {items.map((it, i) => (
          <div key={i}>
            <div style={{display: 'flex', justifyContent: 'space-between', color: C.ink, fontSize: 28, fontWeight: 700, marginBottom: 8}}>
              <span>{it.label}</span><span style={{color: cols[i], fontWeight: 800}}>{it.value}</span>
            </div>
            <div style={{height: 26, borderRadius: 13, background: T.track}}>
              <div style={{height: 26, borderRadius: 13, width: `${Math.max(3, (nums[i] / mx) * 100) * p}%`, background: cols[i]}} />
            </div>
          </div>
        ))}
      </div>
    </Frame>
  );
};

// ---- thẻ chữ: so sánh dạng bảng khi giá trị là chữ hoặc khác đơn vị (không vẽ thanh rỗng) ----
const TextCards: React.FC<{spec: DataSpec; w: number; h: number}> = ({spec, w, h}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = useAccent();
  const items = (spec.items || []).slice(0, 4);
  const two = items.length === 2;
  return (
    <Frame w={w} h={h} title={spec.title || 'So sánh'} sub="Từ bài gốc">
      <div style={{display: 'flex', flexDirection: two ? 'row' : 'column', gap: 18, height: '100%', justifyContent: 'center', alignItems: two ? 'center' : 'stretch'}}>
        {items.map((it, i) => {
          const s = Math.max(0.35, spring({frame: f - i * 6, fps, config: {damping: 14}}));
          return <div key={i} style={{flex: two ? 1 : undefined, height: two ? '78%' : undefined, boxSizing: 'border-box', borderRadius: 18, padding: two ? '26px 28px' : '14px 24px', background: `${ac}14`,
            border: `1.5px solid ${ac}55`, display: 'flex', flexDirection: two ? 'column' : 'row', justifyContent: two ? 'center' : 'space-between',
            alignItems: two ? 'flex-start' : 'center', gap: two ? 16 : 20, opacity: s, transform: `translateY(${(1 - s) * 24}px)`}}>
            <div style={{color: C.muted, fontFamily: HEAD, fontWeight: 700, fontSize: two ? 30 : 28}}>{it.label}</div>
            {it.value ? <div style={{color: C.ink, fontFamily: two ? DISPLAY : HEAD, fontWeight: 800, fontSize: two ? 50 : 32, lineHeight: 1.15,
              textAlign: two ? 'left' : 'right'}}>{it.value}</div> : null}
          </div>;
        })}
      </div>
    </Frame>
  );
};

// ---- checklist ----
const Checklist: React.FC<{spec: DataSpec; w: number; h: number}> = ({spec, w, h}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const items = (spec.items || []).slice(0, 5);
  const ac = useAccent();
  return (
    <Frame w={w} h={h} title={spec.title || 'Checklist'} sub="">
      <div style={{display: 'flex', flexDirection: 'column', gap: 22, justifyContent: 'center', height: '100%'}}>
        {items.map((it, i) => {
          const s = spring({frame: f - 6 - i * 14, fps, config: {damping: 12}});
          return <div key={i} style={{display: 'flex', gap: 20, alignItems: 'center', opacity: s, transform: `translateX(${(1 - s) * 40}px)`}}>
            <div style={{width: 48, height: 48, borderRadius: 12, background: ac, color: '#0A0C12', fontSize: 30, fontWeight: 800,
              display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${s})`}}>✓</div>
            <div style={{color: C.ink, fontSize: 34, fontWeight: 700}}>{it.label}</div>
          </div>;
        })}
      </div>
    </Frame>
  );
};

// hình dữ liệu này có gì để vẽ không (không có → cảnh đó dùng nhịp hình khác, không để khung trống)
export const dataOk = (spec: DataSpec | null | undefined, data: any): boolean => {
  if (!spec || !spec.type || spec.type === 'none') return false;
  if (['stat_compare', 'checklist', 'text_cards'].includes(spec.type)) return (spec.items || []).length > 0;
  if (spec.type === 'coin_chart') {
    if (spec.chart?.series?.length) return true;
    const sym = (spec.tickers?.[0] || '').replace('$', '').toUpperCase();
    return !!(data?.coins?.[sym] || (data?.markets || []).some((x: any) => x.sym === sym));
  }
  if (spec.type === 'fear_greed') return !!data?.fear_greed?.length;
  if (spec.type === 'dominance') return !!data?.global?.dominance;
  if (spec.type === 'market_heatmap') return !!data?.markets?.length;
  return false;
};

export const DataPanel: React.FC<{spec: DataSpec; data: any; w: number; h: number}> = ({spec, data, w, h}) => {
  switch (spec.type) {
    case 'fear_greed': return <FearGreed data={data} w={w} h={h} />;
    case 'dominance': return <Dominance data={data} w={w} h={h} />;
    case 'market_heatmap': return <Heatmap data={data} w={w} h={h} />;
    case 'text_cards': return (spec.items || []).length ? <TextCards spec={spec} w={w} h={h} /> : null;
    case 'coin_chart': {
      if (spec.chart?.series?.length) return <CoinChart data={data} spec={spec} w={w} h={h} />;
      const sym = (spec.tickers?.[0] || '').replace('$', '').toUpperCase();
      const ok = data?.coins?.[sym] || (data?.markets || []).some((x: any) => x.sym === sym);
      return ok ? <CoinChart data={data} spec={spec} w={w} h={h} /> : <Heatmap data={data} w={w} h={h} />;
    }
    case 'stat_compare': return (spec.items || []).length ? <StatCompare spec={spec} w={w} h={h} /> : null;
    case 'checklist': return (spec.items || []).length ? <Checklist spec={spec} w={w} h={h} /> : null;
    default: return null;
  }
};
