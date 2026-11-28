// Máy đo bố cục (Trọng 28/11: "bot kiểm tra đang làm cái quái gì vậy?").
// Chỉ bật khi props.lint = true (lint.mjs). Mỗi khung được dựng: đợi font xong, đo vị trí THẬT của mọi dòng chữ đang hiện,
// rồi in ra console 1 dòng "LAYOUT_JSON {...}": chữ đè chữ, chữ bị cắt hoặc tràn mép, và toàn bộ chữ đang hiện (để soát chính tả).
// Không dùng AI: lỗi trình bày bị bắt chắc chắn, kèm giây cụ thể.
import React, {useEffect} from 'react';
import {continueRender, delayRender, useCurrentFrame, useVideoConfig} from 'remotion';

type Box = {el: Element; text: string; r: DOMRect; vis: number};

const alpha = (c: string) => {
  const m = c.match(/rgba?\(([^)]+)\)/);
  if (!m) return 1;
  const p = m[1].split(/[ ,/]+/).filter(Boolean);
  return p.length >= 4 ? parseFloat(p[3]) : 1;
};

const visibility = (el: Element) => {
  let v = 1;
  let e: Element | null = el;
  while (e && e !== document.body) {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') return 0;
    v *= parseFloat(s.opacity || '1');
    e = e.parentElement;
  }
  return v * alpha(getComputedStyle(el).color);
};

const textBoxes = (): Box[] => {
  const out: Box[] = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Map<Element, Box>();
  let n: Node | null;
  while ((n = walker.nextNode())) {
    const t = (n.textContent || '').trim();
    const el = n.parentElement;
    if (!t || !el || el.closest('[data-probe-skip]')) continue;
    const rg = document.createRange();
    rg.selectNodeContents(n);
    const r = rg.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    const vis = visibility(el);
    if (vis < 0.35) continue;
    const old = seen.get(el);
    if (old) {   // một phần tử có nhiều mẩu chữ: gộp thành 1 khung
      const x0 = Math.min(old.r.left, r.left), y0 = Math.min(old.r.top, r.top);
      old.r = new DOMRect(x0, y0, Math.max(old.r.right, r.right) - x0, Math.max(old.r.bottom, r.bottom) - y0);
      old.text += ' ' + t;
      continue;
    }
    const b = {el, text: t, r, vis};
    seen.set(el, b);
    out.push(b);
  }
  return out;
};

const inter = (a: DOMRect, b: DOMRect) =>
  Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));

const measure = (W: number, H: number) => {
  const bs = textBoxes();
  const issues: {kind: string; text: string; other?: string}[] = [];
  // 1) chữ đè chữ: 2 khối chữ (không lồng nhau) chồng lên nhau quá 12% diện tích khối nhỏ
  for (let i = 0; i < bs.length; i++) {
    for (let j = i + 1; j < bs.length; j++) {
      const a = bs[i], b = bs[j];
      if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
      const ov = inter(a.r, b.r);
      const small = Math.min(a.r.width * a.r.height, b.r.width * b.r.height);
      if (small > 0 && ov / small > 0.12) issues.push({kind: 'de_chu', text: a.text.slice(0, 80), other: b.text.slice(0, 80)});
    }
  }
  // 1b) chữ bị một khối đặc (thẻ, ảnh) che: lấy phần tử nằm trên cùng tại vài điểm trong dòng chữ
  for (const b of bs) {
    const r = b.r;
    const pts = Array.from({length: 11}, (_, k) => [0.04 + k * 0.092, 0.5]);
    let hits = 0, valid = 0, by = '';
    for (const [px, py] of pts) {
      const x = r.left + r.width * px, y = r.top + r.height * py;
      if (x < 0 || y < 0 || x >= W || y >= H) continue;
      valid++;
      const top = document.elementFromPoint(x, y);
      if (!top || top === b.el || b.el.contains(top) || top.contains(b.el)) continue;
      let e: Element | null = top;
      while (e && e !== document.body && !e.contains(b.el)) {
        const s = getComputedStyle(e);
        if (e.tagName === 'IMG' || e.tagName === 'svg' || alpha(s.backgroundColor) * visibility(e) / Math.max(0.01, alpha(s.color)) >= 0.5) {
          hits++;
          by = ((e as HTMLElement).innerText || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40);
          break;
        }
        e = e.parentElement;
      }
    }
    // che hết = cố ý giấu (thẻ phóng to phủ lên), che một phần = lỗi xấu (chữ lòi ra mép thẻ)
    const frac = valid ? hits / valid : 0;
    if (frac > 0.08 && frac < 0.9) issues.push({kind: 'bi_che', text: b.text.slice(0, 80), other: by});
  }
  // 2) chữ bị cắt: nằm ngoài khung cha có overflow hidden, hoặc ra ngoài màn hình
  for (const b of bs) {
    const r = b.r;
    if (r.left < -2 || r.top < -2 || r.right > W + 2 || r.bottom > H + 2) {
      issues.push({kind: 'tran_man_hinh', text: b.text.slice(0, 80)});
      continue;
    }
    let e = b.el.parentElement;
    while (e && e !== document.body) {
      const s = getComputedStyle(e);
      if (s.overflow !== 'visible' || s.overflowX !== 'visible' || s.overflowY !== 'visible') {
        const c = e.getBoundingClientRect();
        if (c.width > 40 && c.height > 20 && (r.left < c.left - 3 || r.right > c.right + 3 || r.top < c.top - 3 || r.bottom > c.bottom + 3)) {
          issues.push({kind: 'chu_bi_cat', text: b.text.slice(0, 80)});
          break;
        }
      }
      e = e.parentElement;
    }
  }
  // 3) một từ mồ côi ở dòng cuối của khối chữ nhiều dòng
  for (const b of bs) {
    const words = b.text.split(/\s+/);
    if (words.length < 4 || b.el.childElementCount > 0) continue;
    const lh = parseFloat(getComputedStyle(b.el).lineHeight) || parseFloat(getComputedStyle(b.el).fontSize) * 1.2;
    if (b.r.height < lh * 1.6) continue;
    const rg = document.createRange();
    const tn = Array.from(b.el.childNodes).find((x) => x.nodeType === 3 && (x.textContent || '').trim());
    if (!tn) continue;
    rg.selectNodeContents(tn);
    const lines = Array.from(rg.getClientRects());
    const last = lines[lines.length - 1];
    const full = Math.max(...lines.map((x) => x.width));
    if (last && full > 0 && last.width / full < 0.16 && !/\d/.test(words[words.length - 1])) {
      issues.push({kind: 'tu_mo_coi', text: b.text.slice(0, 80)});
    }
  }
  return {texts: bs.map((b) => b.text), issues};
};

export const LayoutProbe: React.FC = () => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  useEffect(() => {
    const h = delayRender('layout-probe');
    let done = false;
    const run = () => {
      if (done) return;
      done = true;
      try {
        const m = measure(width, height);
        console.log('LAYOUT_JSON ' + JSON.stringify({f, ...m}));
      } catch (e) {
        console.log('LAYOUT_JSON ' + JSON.stringify({f, error: String(e)}));
      }
      continueRender(h);
    };
    (document as any).fonts?.ready.then(() => requestAnimationFrame(() => requestAnimationFrame(run))) ?? requestAnimationFrame(run);
    const to = setTimeout(run, 4000);
    return () => clearTimeout(to);
  }, [f, width, height]);
  return null;
};
