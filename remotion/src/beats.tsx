import React from 'react';
import {Img, interpolate, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, clamp, CountUp, FONT, useAccent} from './ui';
import {DataPanel} from './data';

// Trọng 21/11: "hình phải ăn khớp lời đọc, sáng tạo hơn". Mỗi phần chia thành nhiều "beat" (nhịp hình),
// mỗi beat bật lên ĐÚNG lúc giọng đọc nói tới cụm từ đó (s = giây trong cảnh), đổi kiểu hình liên tục.
export type Side = {label: string; value: string; logo?: string | null; tone?: 'up' | 'down' | 'flat'; note?: string};
export type Beat = {
  s: number;
  type: 'bignum' | 'versus' | 'dots' | 'flow' | 'statement' | 'chart' | 'logos' | 'question' | 'race' | 'matrix' | 'wma' | 'trend' | 'photo' | 'dow';
  from?: string; k?: number; mode?: 'swings'; n?: number;
  src?: string;
  value?: string; label?: string; logo?: string | null; tone?: 'up' | 'down' | 'flat';
  left?: Side; right?: Side;
  total?: number; hit?: number;
  steps?: string[]; step_s?: (number | null)[];
  text?: string; sub?: string; tag?: string; keyword?: string;
  ticker?: string; tickers?: string[]; days?: number;
  items?: Side[];
  cols?: {label: string; logo?: string | null}[]; rows?: {label: string; marks: string[]}[];
};

// Trọng 23/11: nguồn số liệu ghi nhỏ ở dòng riêng phía dưới, không viết liền vào chú thích ("... năm 2025. Nguồn: SPIVA ...")
export const splitSource = (label?: string, src?: string): [string, string] => {
  const t = String(label || '').trim();
  if (src) return [t, src];
  const m = t.match(/^(.*?)[.,;]?\s*(?:Nguồn|Source)\s*:\s*(.+)$/i);
  if (m) return [m[1].trim(), m[2].replace(/^\((.*)\)$/, '$1').trim()];
  const p = t.match(/^(.*\S)\s*\(([^()]*(?:SPIVA|Yahoo|CoinGecko|S&P Dow|Fidelity|Bloomberg|Reuters|Finhay|HOSE|DefiLlama|Glassnode)[^()]*)\)$/i);
  if (p) return [p[1].trim(), p[2].trim()];
  return [t, ''];
};

const SourceLine: React.FC<{text: string}> = ({text}) => text ? (
  <div style={{position: 'absolute', left: 40, right: 40, bottom: 18, fontSize: 22, fontWeight: 600, color: `${C.muted}AA`,
    whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>Nguồn: {text}</div>
) : null;

const toneColor = (t?: string) => (t === 'down' ? C.red : t === 'up' ? C.green : C.ink);

// Trọng 22/11: VĨNH VIỄN chỉ dùng nền sạch (trắng). Không thẻ nền màu đậm/gradient.
const Card: React.FC<{w: number; h: number; children: React.ReactNode; pad?: number}> = ({w, h, children, pad = 40}) => {
  const ac = useAccent();
  return (
    <div style={{width: w, height: h, borderRadius: 28, background: C.panel, border: `1px solid ${C.line}`, borderTop: `5px solid ${ac}`,
      boxShadow: '0 20px 56px rgba(40,50,110,0.14)', padding: pad, boxSizing: 'border-box', fontFamily: FONT, position: 'relative',
      overflow: 'hidden', display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>{children}</div>
  );
};

const Logo: React.FC<{src?: string | null; size: number; label?: string}> = ({src, size, label}) => {
  const ac = useAccent();
  return src ? <Img src={staticFile(src)} style={{width: size, height: size, borderRadius: 999, boxShadow: '0 8px 22px rgba(40,50,110,0.18)'}} />
    // Trọng 22/11: không còn vòng tròn chữ bị cắt ("45 n", "CapE", "Nvid"). Không có logo thì: ticker ngắn → nhãn đủ chữ; còn lại → không vẽ gì
    : label && /^[A-Z0-9&.$]{2,6}$/.test(label) ? <div style={{minWidth: size, height: size * 0.62, padding: `0 ${size * 0.14}px`, borderRadius: size * 0.2,
      background: '#FFFFFF', border: `${Math.max(3, size * 0.035)}px solid ${ac}`, color: ac, fontWeight: 900, fontSize: size * 0.3,
      display: 'flex', alignItems: 'center', justifyContent: 'center', transform: 'rotate(-6deg)', boxShadow: '0 8px 22px rgba(40,50,110,0.18)'}}>{label}</div>
    : null;
};

const BigNum: React.FC<{b: Beat; w: number; h: number}> = ({b, w, h}) => {
  const [lab, src] = splitSource(b.label, (b as any).source);
  return (
  <Card w={w} h={h}>
    <div style={{display: 'flex', alignItems: 'center', gap: 34}}>
      {b.logo ? <Logo src={b.logo} size={150} label={b.label} /> : null}
      <div style={{display: 'flex', flexDirection: 'column', gap: 12}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
        {(b.tone === 'up' || b.tone === 'down') && /^[~≈]?\s*[+\-−]/.test(String(b.value || '')) ? <svg width="54" height="54" viewBox="0 0 24 24" style={{flexShrink: 0}}>
          <path d={b.tone === 'up' ? 'M4 17 L12 6 L20 17 Z' : 'M4 7 L12 18 L20 7 Z'} fill={toneColor(b.tone)} /></svg> : null}
        <CountUp value={b.value || ''} size={(b.value || '').length > 7 ? Math.max(64, Math.min(96, Math.floor((w - 340) / ((b.value || '').length * 0.62)))) : (b.value || '').length > 5 ? 120 : 150} delay={2} color={toneColor(b.tone)} />
        </div>
        <div style={{fontSize: 38, fontWeight: 700, color: C.muted, maxWidth: b.logo ? w - 300 : w - 110, lineHeight: 1.22, textWrap: 'balance'} as React.CSSProperties}>{lab}</div>
      </div>
    </div>
    <SourceLine text={src} />
  </Card>
  );
};

// cỡ chữ giá trị 2 bên: chữ dài thì co lại cho vừa nửa thẻ (lỗi 23/11: "Điều gì đã vào giá?" tràn mép)
// Trọng 24/11: "$115.8B" dính sát chữ VS: số phải nằm gọn trong nửa thẻ, chừa lề 40px mỗi bên
const fitVs = (v: string, w: number) => Math.max(44, Math.min(88, Math.floor(((w - 200) / 2 - 40) / (Math.max(1, v.length) * 0.62))));

const Versus: React.FC<{b: Beat; w: number; h: number}> = ({b, w, h}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const half = (w - 160) / 2;
  const labs = [b.left?.label || '', b.right?.label || ''];
  // cỡ nhãn chung: vừa 2 dòng trong nửa thẻ cho nhãn dài nhất
  const lbFs = Math.max(26, Math.min(40, Math.floor((half - 20) * 2 / (Math.max(1, ...labs.map((l) => l.length)) * 0.56))));
  // cỡ số chung cho 2 bên (theo số dài hơn) để 2 số cân nhau
  const valFs = Math.min(fitVs(String(b.left?.value ?? ''), w), fitVs(String(b.right?.value ?? ''), w));
  const anyLogo = !!(b.left?.logo || b.right?.logo);
  const anyNote = !!(b.left?.note || b.right?.note);
  // nhãn dài: xuống dòng ở dấu phẩy ("Sau 30 năm, / lãi 10%/năm"), không để máy tự ngắt giữa cụm ("lãi / 10%/năm")
  const nice = (l: string) => {
    const m = l.length * lbFs * 0.56 > half - 20 ? l.match(/^(.+?,)\s+(.+)$/) : null;
    return m ? <><span>{m[1]}</span><span style={{whiteSpace: 'nowrap'}}>{m[2]}</span></> : <span>{l}</span>;
  };
  const side = (x: Side | undefined, i: number) => {
    if (!x) return null;
    // review 27/11: cột phải trượt trễ 3 khung làm 2 số lệch hàng, màu mờ khi bot chụp. 2 bên hiện CÙNG lúc, nhanh, không trượt
    const s = spring({frame: f - 1, fps, config: {damping: 20, mass: 0.6}});
    return (
      <div style={{flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-start', gap: 14, opacity: s,
        transform: `scale(${0.94 + 0.06 * s})`}}>
        {anyLogo ? <div style={{height: 130, display: 'flex', alignItems: 'center'}}><Logo src={x.logo} size={130} label={x.label} /></div> : null}
        {/* Trọng 23/11 "chữ xấu, không thẳng hàng": nhãn 2 bên cùng cỡ chữ, cùng chiều cao khung (tối đa 2 dòng, căn giữa),
            nên 2 con số luôn nằm trên cùng một hàng */}
        <div style={{height: lbFs * 1.25 * 2, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', alignItems: 'center', textAlign: 'center',
          fontSize: lbFs, lineHeight: 1.25, fontWeight: 800, color: C.ink, maxWidth: half - 20, overflow: 'hidden'}}>{nice(x.label)}</div>
        <CountUp value={x.value} size={valFs} delay={2} color={toneColor(x.tone)} />
        {/* Trọng 24/11: số % nhỏ dưới số lớn (vd "+103% so với cùng kỳ"); 2 bên cùng chiều cao nên vẫn thẳng hàng */}
        {anyNote ? <div style={{height: 50, fontSize: 38, fontWeight: 800, color: x.note ? toneColor(x.tone) : 'transparent', whiteSpace: 'nowrap',
          opacity: interpolate(f - 6, [0, 6], [0, 1], clamp)}}>{x.note || '.'}</div> : null}
      </div>
    );
  };
  return (
    <Card w={w} h={h}>
      <div style={{display: 'flex', alignItems: 'flex-start'}}>
        {side(b.left, 0)}
        <div style={{fontSize: 38, fontWeight: 800, color: C.muted, alignSelf: 'flex-end', margin: `0 20px ${valFs * 0.3 + (anyNote ? 40 : 0)}px`}}>VS</div>
        {side(b.right, 1)}
      </div>
      {/* review 26/11: "Vượt kỷ lục tháng 6. Nguồn: ..." viết liền, tách nguồn xuống dòng nhỏ riêng */}
      {splitSource(b.sub, (b as any).source)[0] ? <div style={{textAlign: 'center', marginTop: 22, fontSize: 28, fontWeight: 700, color: C.muted}}>{splitSource(b.sub, (b as any).source)[0]}</div> : null}
      <SourceLine text={splitSource(b.sub, (b as any).source)[1]} />
    </Card>
  );
};

const Dots: React.FC<{b: Beat; w: number; h: number}> = ({b, w, h}) => {
  const f = useCurrentFrame();
  const total = b.total || 10, hit = b.hit || 0;
  const ac = useAccent();
  const cols = Math.min(total, 8);
  const size = Math.min(70, (w - 120) / cols - 14);
  return (
    <Card w={w} h={h}>
      <div style={{display: 'flex', flexWrap: 'wrap', gap: 14, justifyContent: 'center', maxWidth: cols * (size + 14)}}>
        {Array.from({length: total}).map((_, i) => {
          const on = i < hit && f > 4 + i * 1.2;   // review 22/11: tô đủ chấm nhanh, khung tĩnh không thấy số chấm lệch số liệu
          return <div key={i} style={{width: size, height: size, borderRadius: 999, background: on ? C.green : `${C.ink}14`,
            transform: `scale(${on ? 1 : 0.85})`, transition: 'none', boxShadow: on ? `0 0 0 5px ${C.green}22` : 'none'}} />;
        })}
      </div>
      <div style={{display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: 18, marginTop: 30}}>
        <div style={{fontSize: 92, fontWeight: 800, color: ac}}>{hit}/{total}</div>
        <div style={{fontSize: 30, fontWeight: 700, color: C.muted, maxWidth: w - 330, lineHeight: 1.2}}>{splitSource(b.label, (b as any).source)[0]}</div>
      </div>
      <SourceLine text={splitSource(b.label, (b as any).source)[1]} />
    </Card>
  );
};

const Flow: React.FC<{b: Beat; w: number; h: number; t: number; dur: number}> = ({b, w, h, t, dur}) => {
  const ac = useAccent();
  const steps = b.steps || [];
  const each = Math.max(1.2, dur / Math.max(1, steps.length));
  let cur = Math.min(steps.length - 1, Math.floor(t / each));
  if (b.step_s?.some((x) => x !== null && x !== undefined)) {   // có mốc theo lời đọc thì bám mốc
    cur = 0;
    b.step_s.forEach((x, i) => { if (x !== null && x !== undefined && t >= x - 0.1) cur = i; });
  }
  return (
    <Card w={w} h={h} pad={34}>
      {b.label ? <div style={{fontSize: 34, fontWeight: 800, color: C.muted, marginBottom: 18, letterSpacing: 1}}>{b.label}</div> : null}
      <div style={{display: 'flex', flexDirection: 'column', gap: steps.length > 3 ? 12 : 20}}>
        {steps.map((s, i) => {
          const on = i <= cur;
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 18, opacity: on ? 1 : 0.3,
              transform: `translateX(${i === cur ? 10 : 0}px)`}}>
              <div style={{width: 54, height: 54, borderRadius: 16, background: i === cur ? ac : `${ac}22`, color: i === cur ? '#fff' : ac,
                fontWeight: 800, fontSize: 26, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>{i + 1}</div>
              <div style={{fontSize: steps.length > 3 ? (i === cur ? 44 : 38) : (i === cur ? 52 : 44), fontWeight: i === cur ? 800 : 600, color: C.ink, lineHeight: 1.15}}>{s}</div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

const Statement: React.FC<{b: Beat; w: number; h: number; question?: boolean}> = ({b, w, h, question}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = useAccent();
  const s = spring({frame: f - 2, fps, config: {damping: 13}});
  return (
    <Card w={w} h={h} pad={56}>
      {b.logo ? <div style={{position: 'absolute', right: 44, top: 40}}><Logo src={b.logo} size={96} /></div> : null}
      {question ? <div style={{fontSize: 120, fontWeight: 900, color: ac, lineHeight: 0.8, marginBottom: 10}}>?</div>
        : <div style={{fontSize: 120, fontWeight: 900, color: `${ac}55`, lineHeight: 0.6, marginBottom: 10}}>“</div>}
      {/* Trọng 24/11: chữ mồ côi ("quốc / gia"): chia dòng cân nhau */}
      <div style={{fontSize: (b.text || '').length > 40 ? 60 : 74, fontWeight: 800, color: C.ink, lineHeight: 1.18, textWrap: 'balance',
        transform: `scale(${interpolate(s, [0, 1], [0.92, 1])})`, opacity: s, transformOrigin: 'left center'} as React.CSSProperties}>{b.text}</div>
      {/* review 27/11: "Có: / 1, Không: 2" bị máy ngắt giữa cụm. Mỗi câu (tách ở ". ") 1 dòng, dính "Có: 1", "1 = có" */}
      {splitSource(b.sub, (b as any).source)[0] ? <div style={{fontSize: 34, fontWeight: 600, color: C.muted, marginTop: 22}}>
        {splitSource(b.sub, (b as any).source)[0].split(/(?<=[.!?])\s+/).map((ln, k) =>
          <div key={k} style={{textWrap: 'balance'}}>{ln.replace(/([:=])\s+(?=\S{1,4}\b)/g, '$1\u00a0').replace(/\s+=/g, '\u00a0=')}</div>)}
      </div> : null}
      <SourceLine text={splitSource(b.sub, (b as any).source)[1]} />
    </Card>
  );
};

const Logos: React.FC<{b: Beat; w: number; h: number}> = ({b, w, h}) => {
  const f = useCurrentFrame();
  const items = (b.items || []).slice(0, 4);
  return (
    <Card w={w} h={h}>
      {b.label ? <div style={{fontSize: 30, fontWeight: 800, color: C.muted, marginBottom: 26, textAlign: 'center'}}>{b.label}</div> : null}
      <div style={{display: 'flex', justifyContent: 'space-around'}}>
        {items.map((x, i) => {
          const s = interpolate(f - 4 - i * 8, [0, 12], [0, 1], clamp);
          return (
            <div key={i} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, opacity: s, transform: `scale(${0.8 + s * 0.2})`}}>
              <Logo src={x.logo} size={110} label={x.label} />
              <div style={{fontSize: 30, fontWeight: 800, color: C.ink}}>{x.label}</div>
              {x.value ? <div style={{fontSize: 40, fontWeight: 800, color: toneColor(x.tone)}}>{x.value}</div> : null}
            </div>
          );
        })}
      </div>
    </Card>
  );
};

// Trọng 22/11 (review: "thử áp vào HYPE và AAVE" cần bảng tick): bảng so sánh nhiều tiêu chí, từng dòng hiện dần
const Matrix: React.FC<{b: Beat; w: number; h: number}> = ({b, w, h}) => {
  const f = useCurrentFrame();
  const cols = (b.cols || []).slice(0, 3), rows = (b.rows || []).slice(0, 5);
  const mark = (m: string) => m === '✓' ? {c: C.green, t: '✓'} : m === '✗' ? {c: C.red, t: '✗'} : {c: '#E8A317', t: m || '~'};
  const cw = 190;
  return (
    <Card w={w} h={h} pad={36}>
      {b.label ? <div style={{fontSize: 30, fontWeight: 800, color: C.muted, marginBottom: 18}}>{b.label}</div> : null}
      <div style={{display: 'flex', alignItems: 'center', paddingBottom: 14, borderBottom: `2px solid ${C.line}`}}>
        <div style={{flex: 1}} />
        {cols.map((c, i) => <div key={i} style={{width: cw, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8}}>
          <Logo src={c.logo} size={72} label={c.label} /><div style={{fontSize: 30, fontWeight: 800, color: C.ink}}>{c.label}</div></div>)}
      </div>
      {rows.map((r, i) => {
        const s = interpolate(f - 6 - i * 14, [0, 10], [0, 1], clamp);
        return <div key={i} style={{display: 'flex', alignItems: 'center', padding: '16px 0', borderBottom: `1px solid ${C.line}`, opacity: s}}>
          <div style={{flex: 1, fontSize: 34, fontWeight: 700, color: C.ink}}>{r.label}</div>
          {cols.map((_, j) => { const m = mark(r.marks[j]); return <div key={j} style={{width: cw, textAlign: 'center', fontSize: m.t.length > 1 ? 34 : 52, fontWeight: 900,
            color: m.c, transform: `scale(${0.6 + 0.4 * s})`}}>{m.t}</div>; })}
        </div>;
      })}
      {b.sub ? <div style={{marginTop: 14, fontSize: 24, fontWeight: 600, color: C.muted}}>{b.sub}</div> : null}
    </Card>
  );
};

// Trọng 24/11 "thêm nhiều ảnh hơn": ảnh kho (Pixabay/Pexels, không ảnh người thật có tên) phủ kín thẻ, zoom chậm, chú thích dưới
const Photo: React.FC<{b: Beat; w: number; h: number}> = ({b, w, h}) => {
  const f = useCurrentFrame();
  const ac = useAccent();
  const z = interpolate(f, [0, 150], [1.04, 1.14], clamp);
  return (
    <div style={{width: w, height: h, borderRadius: 28, overflow: 'hidden', position: 'relative', borderTop: `5px solid ${ac}`,
      boxShadow: '0 20px 56px rgba(40,50,110,0.14)', background: C.panel, fontFamily: FONT}}>
      {b.src ? <Img src={staticFile(b.src)} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${z})`}} /> : null}
      {b.label ? <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, padding: '60px 36px 28px',
        background: 'linear-gradient(rgba(15,20,45,0), rgba(15,20,45,0.92) 45%)', color: '#FFFFFF', fontSize: 44, fontWeight: 800, lineHeight: 1.15,
        textWrap: 'balance', textShadow: '0 2px 8px rgba(0,0,0,0.45)', opacity: interpolate(f, [4, 14], [0, 1], clamp)} as React.CSSProperties}>{b.label}</div> : null}
    </div>
  );
};

// Chọn beat đang chạy theo thời gian t (giây trong cảnh)
export const BeatPanel: React.FC<{beats: Beat[]; t: number; sceneDur: number; data: any; w: number; h: number}> = ({beats, t, sceneDur, data, w, h}) => {
  const {fps} = useVideoConfig();
  const list = [...beats].sort((a, b) => a.s - b.s);
  let i = -1;
  list.forEach((b, k) => { if (t >= b.s - 0.15) i = k; });
  if (i < 0) i = 0;
  // review 26/11: trước thẻ đầu tiên không để màn trống (từng trống 5 giây đầu): thẻ đầu hiện từ giây 0
  const b = i === 0 && t < list[0].s ? {...list[0], s: 0} : list[i];
  const end = list[i + 1]?.s ?? sceneDur;
  const local = t - b.s;
  const inP = interpolate(local, [-0.12, 0.06], [0, 1], clamp);   // review 26/11: chuyển thẻ nhanh (khoảng 0,15 giây), không còn chữ xám mờ
  const body = (() => {
    switch (b.type) {
      case 'bignum': return <BigNum b={b} w={w} h={h} />;
      case 'photo': return b.src ? <Photo b={b} w={w} h={h} /> : <Statement b={{...b, text: b.label || ''}} w={w} h={h} />;
      case 'versus': return <Versus b={b} w={w} h={h} />;
      case 'dots': return <Dots b={b} w={w} h={h} />;
      case 'flow': return <Flow b={b} w={w} h={h} t={Math.max(0, local)} dur={end - b.s} />;
      case 'logos': return <Logos b={b} w={w} h={h} />;
      case 'question': return <Statement b={b} w={w} h={h} question />;
      case 'matrix': return <Matrix b={b} w={w} h={h} />;
      case 'race': return <Race b={b} w={w} h={h} data={data} />;
      case 'trend': return data?.trends?.[b.keyword || 'Bitcoin']?.values?.length ? <Trend b={b} w={w} h={h} data={data} /> : <Statement b={{...b, text: b.label || 'Google Trends'}} w={w} h={h} />;
      case 'dow': { const dk = `${b.from || '2018'}:${b.k || 4}`;
        return data?.dow?.[dk]?.price?.length ? <Dow b={b} w={w} h={h} d={data.dow[dk]} /> : <Statement b={{...b, text: b.label || 'Lý thuyết Dow'}} w={w} h={h} />; }
      case 'wma': return data?.wma?.price?.length ? <Wma b={b} w={w} h={h} data={data} /> : <Statement b={{...b, text: b.label || '200WMA'}} w={w} h={h} />;
      case 'chart': {
        // Trọng 24/11: hook từng hiện khung "Top coin · 7 ngày" TRỐNG vì biểu đồ không có dữ liệu. Không có giá thì hiện thẻ chữ, không bao giờ khung rỗng
        const sym = String(b.ticker || '').replace('$', '').toUpperCase();
        const ok = sym && (data?.coins?.[sym] || (data?.markets || []).some((x: any) => x.sym === sym));
        return ok ? <DataPanel spec={{type: 'coin_chart', tickers: [sym], title: b.label}} data={data} w={w} h={h} />
          : <Statement b={{...b, text: b.text || b.label || sym}} w={w} h={h} />;
      }
      default: return <Statement b={b} w={w} h={h} />;
    }
  })();
  // mỗi beat là một "cảnh con": Sequence-like bằng cách reset frame qua key
  return (
    <div key={i} style={{opacity: inP, transform: `translateY(${(1 - inP) * 24}px) scale(${1 + Math.max(0, local) * 0.004})`}}>
      <FrameShift from={Math.round(b.s * fps)}>{body}</FrameShift>
    </div>
  );
};

// Trọng 22/11 (review: "chủ đề là giá mà chưa có biểu đồ"): 2-3 coin cùng xuất phát 0%, đường % chạy dần, số cuối to
const Race: React.FC<{b: Beat; w: number; h: number; data: any}> = ({b, w, h, data}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const coins = (b.tickers || []).map((t) => ({t, c: (data?.coins || {})[t.replace('$', '').toUpperCase()]})).filter((x) => x.c?.series?.length > 5);
  const pad = {l: 40, r: 230, t: 96, b: 56};
  const W = w - pad.l - pad.r, H = h - pad.t - pad.b;
  const lines = coins.map(({t, c}) => {
    const n = c.series.length, k = Math.max(2, Math.round(n * Math.min(1, (b.days || c.days || n) / Math.max(1, c.days || n))));
    const ser: number[] = c.series.slice(-k);
    return {t, logo: c.logo, color: c.color || C.ink, pct: ser.map((v) => (v / ser[0] - 1) * 100)};
  });
  const all = lines.flatMap((l) => l.pct).concat([0]);
  const lo = Math.min(...all), hi = Math.max(...all);
  const y = (v: number) => pad.t + H - ((v - lo) / Math.max(1e-6, hi - lo)) * H;
  const prog = interpolate(f, [6, Math.round(fps * 3.2)], [0, 1], clamp);   // Trọng 22/11: chạy chậm để người xem kịp theo
  return (
    <Card w={w} h={h} pad={0}>
      <div style={{position: 'absolute', left: 40, top: 28, fontSize: w >= 1300 ? 42 : 38, fontWeight: 800, color: C.ink}}>{b.label}</div>
      <div style={{position: 'absolute', right: 40, top: 26, display: 'flex', gap: 26}}>
        {lines.map((l) => <div key={l.t} style={{display: 'flex', alignItems: 'center', gap: 10}}>
          <div style={{width: 30, height: 7, borderRadius: 4, background: l.color}} /><Logo src={l.logo} size={40} label={l.t} />
          <div style={{fontSize: 30, fontWeight: 800, color: C.ink}}>{l.t}</div></div>)}
      </div>
      <svg width={w} height={h} style={{position: 'absolute', inset: 0}}>
        <line x1={pad.l} x2={pad.l + W} y1={y(0)} y2={y(0)} stroke={C.line} strokeWidth={2} strokeDasharray="8 8" />
        {lines.map((l) => {
          const m = Math.max(2, Math.round(l.pct.length * prog));
          const pts = l.pct.slice(0, m).map((v, i) => `${pad.l + (i / (l.pct.length - 1)) * W},${y(v)}`).join(' ');
          return <polyline key={l.t} points={pts} fill="none" stroke={l.color} strokeWidth={7} strokeLinejoin="round" strokeLinecap="round" />;
        })}
      </svg>
      {lines.map((l) => {
        const v = l.pct[l.pct.length - 1];   // review 22/11: chỉ hiện SỐ CUỐI (số đang chạy trông như số liệu khác)
        return <div key={l.t} style={{position: 'absolute', left: pad.l + W + 18, top: y(v) - 34, display: 'flex', alignItems: 'center', gap: 10,
          opacity: interpolate(prog, [0.45, 0.7], [0, 1], clamp)}}>
          <Logo src={l.logo} size={48} label={l.t} />
          <div style={{fontWeight: 800, fontSize: 44, color: v < 0 ? C.red : C.green, whiteSpace: 'nowrap'}}>{v >= 0 ? '+' : '-'}{Math.abs(v) >= 10 ? 5 * Math.round(Math.abs(v) / 5) : Math.round(Math.abs(v))}%</div>
        </div>;
      })}
      {b.sub ? <div style={{position: 'absolute', left: 40, bottom: 16, fontSize: 24, fontWeight: 600, color: C.muted}}>{b.sub}</div> : null}
    </Card>
  );
};

// Trọng 24/11: biểu đồ Google Trends THẬT (insight_lab.trend_data), đánh dấu điểm thấp nhất từ 2020 và hiện tại.
const Trend: React.FC<{b: Beat; w: number; h: number; data: any}> = ({b, w, h, data}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const d = data.trends[b.keyword || 'Bitcoin'];
  const v: number[] = d.values, dates: string[] = d.dates, n = v.length;
  const pad = {l: 60, r: 70, t: 130, b: 118};
  const W = w - pad.l - pad.r, H = h - pad.t - pad.b;
  const x = (i: number) => pad.l + (i / (n - 1)) * W;
  const y = (val: number) => pad.t + H - (val / 100) * H;
  const prog = interpolate(f, [2, Math.round(fps * 1.8)], [0, 1], clamp);
  const m = Math.max(2, Math.round(n * prog));
  const pts = v.slice(0, m).map((val, i) => `${x(i).toFixed(1)},${y(val).toFixed(1)}`).join(' ');
  const area = `${x(0)},${y(0)} ${pts} ${x(m - 1)},${y(0)}`;
  let kMin = -1;
  dates.forEach((dt, i) => { if (dt >= '2020' && (kMin < 0 || v[i] <= v[kMin])) kMin = i; });
  const years = dates.map((dt, i) => [dt.slice(0, 4), i] as [string, number]).filter(([yr], j, a) => j > 0 && yr !== a[j - 1][0])
    .filter(([yr]) => w >= 1300 || Number(yr) % 2 === 0);
  const on = interpolate(prog, [0.92, 1], [0, 1], clamp);
  const ac = '#4F5BD5';
  return (
    <Card w={w} h={h} pad={0}>
      <div style={{position: 'absolute', left: 40, top: 28, fontSize: w >= 1300 ? 42 : 38, fontWeight: 800, color: C.ink}}>{b.label || `Google Trends: ${b.keyword || 'Bitcoin'}`}</div>
      <div style={{position: 'absolute', left: 40, top: 80, fontSize: 26, fontWeight: 600, color: C.muted}}>Mức quan tâm tìm kiếm toàn cầu, 100 = cao nhất</div>
      <svg width={w} height={h} style={{position: 'absolute', inset: 0}}>
        {years.map(([yr, i]) => <g key={yr}>
          <line x1={x(i)} x2={x(i)} y1={pad.t} y2={pad.t + H} stroke={C.line} strokeWidth={2} />
          <text x={x(i) + 8} y={pad.t + H + 36} fontSize={30} fontWeight={700} fill={C.muted} fontFamily={FONT}>{yr}</text></g>)}
        <polygon points={area} fill={ac} opacity={0.1} />
        <polyline points={pts} fill="none" stroke={ac} strokeWidth={6} strokeLinejoin="round" strokeLinecap="round" />
        {kMin >= 0 ? <g opacity={on}>
          <circle cx={x(kMin)} cy={y(v[kMin])} r={15} fill="#fff" stroke={C.red} strokeWidth={6} />
        </g> : null}
      </svg>
      {kMin >= 0 ? <div style={{position: 'absolute', right: Math.max(30, w - x(kMin) - 60), top: pad.t + 10, fontSize: w >= 1300 ? 40 : 32,
        padding: '6px 18px', borderRadius: 14, background: '#fff', border: `3px solid ${C.red}`, boxShadow: '0 6px 18px rgba(40,50,110,0.12)',
        fontWeight: 900, color: C.red, opacity: on, whiteSpace: 'nowrap'}}>{b.tag || 'Thấp nhất từ 2020'} ↓</div> : null}
      {kMin >= 0 ? <svg width={w} height={h} style={{position: 'absolute', inset: 0, opacity: on}}>
        <line x1={x(kMin)} x2={x(kMin)} y1={pad.t + 70} y2={y(v[kMin]) - 18} stroke={C.red} strokeWidth={3} strokeDasharray="8 8" /></svg> : null}
      <div style={{position: 'absolute', left: 40, bottom: 14, fontSize: 24, fontWeight: 600, color: C.muted}}>
        {b.sub || `Dữ liệu thật: Google Trends, tới ${dates[n - 1].slice(5, 7)}/${dates[n - 1].slice(0, 4)}`}</div>
    </Card>
  );
};

// Trọng 27/11: chart lý thuyết Dow trên giá BTC tuần THẬT (insight_lab.dow_data, cùng quy tắc đỉnh đáy với dow() của radar-scanner).
// Đánh dấu đỉnh/đáy HH, HL (xanh) và LH, LL (đỏ). Trọng 28/11: bỏ hẳn kiểu backtest.
export const Dow: React.FC<{b: Beat; w: number; h: number; d: any}> = ({b, w, h, d}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const px: number[] = d.price, dates: string[] = d.dates, n = px.length;
  const big = w >= 1300;
  const pad = {l: 40, r: big ? 60 : 40, t: 120, b: 118};
  const W = w - pad.l - pad.r, H = h - pad.t - pad.b;
  const lo = Math.log(Math.min(...px) * 0.9), hi = Math.log(Math.max(...px) * 1.08);
  const x = (i: number) => pad.l + (i / (n - 1)) * W;
  const y = (v: number) => pad.t + H - ((Math.log(v) - lo) / (hi - lo)) * H;
  const prog = interpolate(f, [2, Math.round(fps * 2.2)], [0, 1], clamp);
  const m = Math.max(2, Math.round(n * prog));
  const line = px.slice(0, m).map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
  const shown = (i: number) => i < m;
  const years = dates.map((dt, i) => [dt.slice(0, 4), i] as [string, number]).filter(([yr], j, a) => j > 0 && yr !== a[j - 1][0])
    .filter(([yr]) => big || Number(yr) % 2 === 0);
  const sw: any[] = (d.swings || []).slice(-(b.n || (big ? 14 : 10)));
  const BTC = '#F7931A';
  return (
    <Card w={w} h={h} pad={0}>
      <div style={{position: 'absolute', left: 40, top: 28, right: 40, fontSize: big ? 42 : 38, fontWeight: 800, color: C.ink}}>
        {b.label || 'BTC khung tuần: đỉnh và đáy'}</div>
      <svg width={w} height={h} style={{position: 'absolute', inset: 0}}>
        {years.map(([yr, i]) => <g key={yr}>
          <line x1={x(i)} x2={x(i)} y1={pad.t} y2={pad.t + H} stroke={C.line} strokeWidth={2} />
          <text x={x(i) + 8} y={pad.t + H + 34} fontSize={28} fontWeight={700} fill={C.muted} fontFamily={FONT}>{yr}</text></g>)}
        <polyline points={line} fill="none" stroke={BTC} strokeWidth={5} strokeLinejoin="round" strokeLinecap="round" />
        {sw.map((s, k) => shown(s.i) ? <g key={k}>
          <circle cx={x(s.i)} cy={y(s.v)} r={11} fill="#fff" stroke={/^H[HL]$/.test(s.label) ? C.green : C.red} strokeWidth={5} />
          <text x={x(s.i)} y={y(s.v) + (s.tp === 'H' ? -22 : 44)} textAnchor="middle" fontSize={big ? 30 : 28} fontWeight={900}
            fill={/^H[HL]$/.test(s.label) ? C.green : C.red} fontFamily={FONT}>{s.label}</text></g> : null)}
      </svg>
      <div style={{position: 'absolute', left: 40, bottom: 14, fontSize: 24, fontWeight: 600, color: C.muted}}>
        {b.sub || 'Dữ liệu thật: BTC đóng cửa tuần, đỉnh đáy xác định tự động theo Dow'}</div>
    </Card>
  );
};

// Trọng 23/11 (video 100y): giá BTC theo tuần + đường trung bình 200 tuần, 350 tuần. Dữ liệu thật (insight_lab.wma_data).
// Trục giá dạng log để thấy rõ cả đáy 2022 lẫn hiện tại; giá chạy trước, 2 đường trung bình hiện sau.
const Wma: React.FC<{b: Beat; w: number; h: number; data: any}> = ({b, w, h, data}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const d = data.wma;
  const px: number[] = d.price, m2: (number | null)[] = d.ma200, m3: (number | null)[] = d.ma350, dates: string[] = d.dates;
  const n = px.length;
  const pad = {l: 40, r: 280, t: 120, b: 118};
  const W = w - pad.l - pad.r, H = h - pad.t - pad.b;
  const vals = [...px, ...(m2.filter((v) => v) as number[]), ...(m3.filter((v) => v) as number[])];
  const lo = Math.log(Math.min(...vals) * 0.92), hi = Math.log(Math.max(...vals) * 1.04);
  const x = (i: number) => pad.l + (i / (n - 1)) * W;
  const y = (v: number) => pad.t + H - ((Math.log(v) - lo) / (hi - lo)) * H;
  const prog = interpolate(f, [2, Math.round(fps * 1.8)], [0, 1], clamp);   // Trọng 24/11: vẽ xong nhanh, giữ khung lâu
  const maP = interpolate(f, [Math.round(fps * 1.4), Math.round(fps * 2.6)], [0, 1], clamp);
  const line = (arr: (number | null)[], p: number) => {
    const m = Math.max(2, Math.round(n * p));
    return arr.slice(0, m).map((v, i) => (v ? `${x(i).toFixed(1)},${y(v).toFixed(1)}` : '')).filter(Boolean).join(' ');
  };
  const BTC = '#F7931A', C2 = '#4F5BD5', C3 = '#9B51E0';
  // đáy 2022
  let k22 = -1;
  dates.forEach((dt, i) => { if (dt.startsWith('2022') && (k22 < 0 || px[i] < px[k22])) k22 = i; });
  const years = dates.map((dt, i) => [dt.slice(0, 4), i] as [string, number]).filter(([yr, i], j, a) => j > 0 && yr !== a[j - 1][0])
    .filter(([yr]) => w >= 1300 || Number(yr) % 2 === 0);
  // nhãn cuối đường: tránh đè nhau
  const ends = [{t: 'BTC', c: BTC, v: px[n - 1]}, {t: '200WMA', c: C2, v: m2[n - 1] || 0}, {t: '350WMA', c: C3, v: m3[n - 1] || 0}]
    .filter((e) => e.v).map((e) => ({...e, yy: y(e.v)})).sort((a, b2) => a.yy - b2.yy);
  for (let i = 1; i < ends.length; i++) if (ends[i].yy - ends[i - 1].yy < 52) ends[i].yy = ends[i - 1].yy + 52;
  const lastOn = interpolate(prog, [0.9, 1], [0, 1], clamp);
  return (
    <Card w={w} h={h} pad={0}>
      <div style={{position: 'absolute', left: 40, top: 28, fontSize: w >= 1300 ? 42 : 38, fontWeight: 800, color: C.ink}}>{b.label || 'BTC và đường trung bình 200 tuần'}</div>
      {w >= 1300 ? <div style={{position: 'absolute', right: 40, top: 32, display: 'flex', gap: 24, fontSize: 28, fontWeight: 700, color: C.muted}}>
        {[['Giá BTC (tuần)', BTC], ['200WMA', C2], ['350WMA', C3]].map(([t, c]) => (
          <div key={t} style={{display: 'flex', alignItems: 'center', gap: 8}}><div style={{width: 28, height: 7, borderRadius: 4, background: c}} />{t}</div>))}
      </div> : null}
      <svg width={w} height={h} style={{position: 'absolute', inset: 0}}>
        {years.map(([yr, i]) => <g key={yr}>
          <line x1={x(i)} x2={x(i)} y1={pad.t} y2={pad.t + H} stroke={C.line} strokeWidth={2} />
          <text x={x(i) + 8} y={pad.t + H + 34} fontSize={30} fontWeight={700} fill={C.muted} fontFamily={FONT}>{yr}</text></g>)}
        <polyline points={line(m3, maP)} fill="none" stroke={C3} strokeWidth={6} strokeDasharray="14 10" strokeLinecap="round" opacity={maP} />
        <polyline points={line(m2, maP)} fill="none" stroke={C2} strokeWidth={6} strokeLinecap="round" opacity={maP} />
        <polyline points={line(px, prog)} fill="none" stroke={BTC} strokeWidth={5} strokeLinejoin="round" strokeLinecap="round" />
        {k22 >= 0 ? <g opacity={interpolate(prog, [k22 / n, k22 / n + 0.08], [0, 1], clamp)}>
          <circle cx={x(k22)} cy={y(px[k22])} r={14} fill="#fff" stroke={C.red} strokeWidth={5} />
          <text x={x(k22)} y={y(px[k22]) + 50} textAnchor="middle" fontSize={32} fontWeight={800} fill={C.red} fontFamily={FONT}>Đáy 2022</text></g> : null}
        <circle cx={x(n - 1)} cy={y(px[n - 1])} r={14 * lastOn} fill="#fff" stroke={BTC} strokeWidth={5} />
      </svg>
      {b.tag ? <div style={{position: 'absolute', right: pad.r + 10, top: pad.t + H - 76, fontSize: w >= 1300 ? 40 : 34, padding: '6px 18px',
        borderRadius: 14, background: '#fff', border: `3px solid ${/^[+]/.test(b.tag) ? C.green : C.red}`, boxShadow: '0 6px 18px rgba(40,50,110,0.12)',
        fontWeight: 900, color: /^[+]/.test(b.tag) ? C.green : C.red, opacity: maP, whiteSpace: 'nowrap'}}>{b.tag}</div> : null}
      {ends.map((e) => <div key={e.t} style={{position: 'absolute', left: pad.l + W + 26, top: e.yy - 24, fontSize: 36, fontWeight: 800, color: e.c,
        whiteSpace: 'nowrap', opacity: e.t === 'BTC' ? lastOn : maP}}>{e.t}</div>)}
      <div style={{position: 'absolute', left: 40, bottom: 14, fontSize: 24, fontWeight: 600, color: C.muted}}>
        {b.sub || 'Dữ liệu thật: giá BTC đóng cửa theo tuần, trục giá dạng log'}</div>
    </Card>
  );
};

// cho con dùng useCurrentFrame() tính từ lúc beat bắt đầu
const FrameShift: React.FC<{from: number; children: React.ReactNode}> = ({from, children}) => (
  <Sequence from={from} layout="none">{children}</Sequence>
);
