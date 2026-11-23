#!/usr/bin/env python3
"""
Dựng video Smart Penguin Insights từ "nguyên liệu" (insight_lab.py) bằng Remotion, kiểu "dữ liệu thật":

  python insight_render.py --lab lab/<tag> --out out/            → video dài 16:9 + các video ngắn 9:16

Mỗi phần dùng màu nhận diện của dự án được nhắc; phụ đề hiện theo cụm câu; nguồn ghi "Source: @...".
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import podcast as P
import video as V
import music as MU

log = P.log
SR = V.SR
ROOT = Path(__file__).resolve().parent
RD = ROOT / "remotion" / "public"
OVERRIDE = {}
try:
    from insight_lab import BRAND_OVERRIDE as OVERRIDE  # noqa
except Exception:
    pass


def load_lab(lab: Path, voice: str | None = None):
    plan = json.loads((lab / "plan.json").read_text(encoding="utf-8"))
    voice = voice or plan.get("voice") or next(k for k, v in plan["voices"].items() if v)
    vdir = plan["voices"].get(voice)
    if not vdir:
        raise SystemExit(f"Không có audio cho giọng {voice}")
    pcm = {p["key"]: V.file_to_pcm(lab / "audio" / vdir / f"{i:02d}.wav") for i, p in enumerate(plan["parts"])}
    text = {p["key"]: p["text"] for p in plan["parts"]}
    data = json.loads((lab / "data.json").read_text(encoding="utf-8")) if (lab / "data.json").exists() else {}
    return plan, pcm, text, data, voice


def speed(pcm: bytes, factor: float) -> bytes:
    if abs(factor - 1) < 0.01:
        return pcm
    return P._ffmpeg_pcm(["-f", "s16le", "-ar", str(SR), "-ac", "1"], pcm, f"atempo={factor:.3f}")


def word_times(text: str, pcm: bytes) -> list[dict]:
    """Thời điểm từng chữ: chia theo câu (bám chỗ ngừng thật), trong câu chia theo độ dài chữ."""
    sents = [s for s in re.split(r"(?<=[.!?…,;:])\s+", V.en_money(text).strip()) if s]
    if not sents:
        return []
    speech = len(pcm) / SR / 2
    bounds = V.chunk_bounds({"pcm": pcm}, [s.split() for s in sents], speech)
    out = []
    for s, (a, b) in zip(sents, bounds):
        ws = s.split()
        lens = [len(w) + 2 for w in ws]
        tot = sum(lens)
        acc = 0
        for w, L in zip(ws, lens):
            s0 = a + (b - a) * acc / tot
            acc += L
            out.append({"t": w, "s": round(s0, 3), "e": round(a + (b - a) * acc / tot, 3)})
    return out


def build_timeline(plan, pcm, text, gap=0.35, pre: dict | None = None):
    """Ghép audio các đoạn (nghỉ ngắn giữa đoạn để giữ nhịp) + lập danh sách cảnh (giây)."""
    secs = plan["sections"]
    order = (["hook"] if "hook" in pcm else []) + ["intro"] + [f"s{k}" for k in range(len(secs))] + ["outro"]
    audio, scenes, t = b"", [], 0.0
    for key in order:
        a = pcm[key] + V.gap(gap if key != "outro" else 2.6)
        dur = len(a) / SR / 2
        scenes.append({"key": key, "from": round(t, 3), "dur": round(dur, 3), "words": (pre or {}).get(key) or word_times(text[key], pcm[key])})
        audio += a
        t += dur
    return audio, scenes, t


def music_breaks(plan: dict, pcm: dict, text: dict) -> tuple[dict, dict, list]:
    """Trọng 22/11: "đôi lúc có thể chèn nhạc nền, không nhất thiết đọc liên tục".
    Beat có "music": giây → sau câu chứa cụm "at", giọng nghỉ đúng số giây đó và NHẠC NỀN DÂNG LÊN (không bao giờ là im lặng trơn).
    Mốc chữ tính trên giọng gốc rồi dời phần sau đi đúng khoảng nghỉ, nên hình vẫn khớp lời."""
    pre, breaks = {}, {}
    for i, sec in enumerate(plan.get("sections") or []):
        k = f"s{i}"
        mus = [b for b in (sec.get("beats") or []) if b.get("music") and b.get("at")]
        if k not in pcm or not mus:
            continue
        wt = word_times(text[k], pcm[k])
        toks = [_norm(w["t"]) for w in wt]
        cuts = []
        for b in mus:
            ph = [_norm(x) for x in str(b["at"]).split() if _norm(x)]
            j = next((x for x in range(len(toks) - len(ph) + 1) if toks[x:x + len(ph)] == ph), -1)
            if j < 0:
                log(f"   ! nghỉ nhạc '{b['at']}': không thấy trong lời đọc")
                continue
            e = next((x for x in range(j, len(wt)) if re.search(r"[.!?…]$", wt[x]["t"])), len(wt) - 1)
            cuts.append((round(wt[e]["e"] + 0.2, 2), min(4.0, float(b["music"]))))
        a, ws = pcm[k], [dict(w) for w in wt]
        for at, d in sorted(cuts, reverse=True):
            pos = min(len(a), int(at * SR) * 2)
            a = a[:pos] + V.gap(d) + a[pos:]
            for w in ws:
                if w["s"] >= at:
                    w["s"] = round(w["s"] + d, 3)
                    w["e"] = round(w["e"] + d, 3)
            log(f"   Nghỉ nhạc {d:.1f}s ở phần {i + 1} (giây {at:.1f})")
        pcm[k], pre[k], breaks[k] = a, ws, sorted(cuts)
    return pcm, pre, breaks


def mix_music(voice_wav: Path, out_wav: Path, seconds: float, seed: int, swell: list | None = None):
    """Nhạc nền tự nhỏ đi khi có giọng, chuẩn âm lượng YouTube. swell = [(giây bắt đầu, độ dài)] nhạc dâng lên lúc giọng nghỉ."""
    raw = MU.make_music(seconds + 1, seed)
    tmp = out_wav.with_suffix(".pcm")
    tmp.write_bytes(raw.tobytes() if hasattr(raw, "tobytes") else raw)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(voice_wav), "-f", "s16le", "-ar", str(SR), "-ac", "1",
                    "-i", str(tmp), "-filter_complex",
                    f"[1:a]lowpass=f=3200,volume='{_swell_expr(swell)}':eval=frame[m];[0:a]asplit=2[v1][v2];"
                    "[m][v1]sidechaincompress=threshold=0.015:ratio=6:attack=20:release=450[md];"
                    "[v2][md]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
                    "-map", "[a]", "-ar", "48000", str(out_wav)], check=True)
    tmp.unlink()



def _swell_expr(swell: list | None) -> str:
    base = "0.2"
    terms = [f"clip((t-{a:.2f})/0.5,0,1)*clip(({a + d:.2f}-t)/0.6,0,1)" for a, d in (swell or [])]
    return base + ("+0.45*(" + "+".join(terms) + ")" if terms else "")


def _norm(w: str) -> str:
    return re.sub(r"[^\w%$/]", "", w.lower())


def at_time(words: list, phrase: str, start: float = 0.0) -> float | None:
    """Giây giọng đọc nói tới cụm từ (tính từ đầu cảnh)."""
    ws = [_norm(w["t"]) for w in words]
    ph = [_norm(x) for x in str(phrase).split() if _norm(x)]
    for i in range(len(ws) - len(ph) + 1):
        if ph and words[i]["s"] >= start and ws[i:i + len(ph)] == ph:
            return round(words[i]["s"], 2)
    log(f"   ! cụm '{phrase}' không khớp lời đọc mở đầu")
    return None


def hook_impact(hi: dict, words: list, dur: float) -> dict:
    """Màn mở đầu kiểu cú sốc (HookImpact): số lớn, thẻ tài sản bật theo lời, rồi câu hỏi lớn."""
    chips, last = [], 0.0
    for i, c in enumerate(hi.get("chips") or []):
        t = at_time(words, c.get("at", ""), last)
        t = t if t is not None else 2.5 + i * 0.9
        last = t
        chips.append({"text": P.nodash(c["text"]), "s": t})
    q = at_time(words, hi.get("q_at", ""), last) or max(last + 1.2, dur * 0.6)
    sub = at_time(words, hi.get("sub_at", ""), q) if hi.get("sub_at") else None
    return {"value": V.en_money(hi.get("value", "")), "label": P.nodash(hi.get("label", "")), "tag": P.nodash(hi.get("tag", "")),
            "chips": chips, "question": P.nodash(hi.get("question", "")), "sub": P.nodash(hi.get("sub", "")),
            "qAt": q, "subAt": sub if sub is not None else q + 1.2, "tone": hi.get("tone", "down")}


def sign_tone(x: dict) -> dict:
    """Màu số theo dấu (Trọng 23/11: +356% phải xanh, không để đỏ): số tăng (+) xanh, số giảm (-) đỏ.
    Muốn giữ màu riêng thì đặt "tone_lock": true."""
    if not isinstance(x, dict) or x.get("tone_lock"):
        return x
    v = str(x.get("value") or "").strip().lstrip("~≈").strip()
    if v[:1] == "+":
        x = {**x, "tone": "up"}
    elif v[:1] in "-−" and len(v) > 1:
        x = {**x, "tone": "down"}
    return x


def beats_for(beats: list, words: list, dur: float, data: dict) -> list:
    """Gắn mỗi nhịp hình vào ĐÚNG lúc giọng đọc nói cụm từ "at" (Trọng 21/11: hình phải khớp lời)."""
    ws = [_norm(w["t"]) for w in words]
    coins = data.get("coins") or {}

    def logo(x):
        if isinstance(x, dict) and x.get("logo"):
            t = str(x["logo"]).lstrip("$").upper()
            x = {**x, "logo": (coins.get(t) or {}).get("logo")}
        return x
    out, last = [], -1
    for k, b in enumerate(beats):
        ph = [_norm(x) for x in str(b.get("at", "")).split() if _norm(x)]
        s = None
        for i in range(last + 1, len(ws) - len(ph) + 1):
            if ph and ws[i:i + len(ph)] == ph:
                s, last = words[i]["s"], i
                break
        if s is None:   # không khớp: rải đều
            s = dur * k / max(1, len(beats))
            log(f"   ! nhịp hình '{b.get('at')}' không khớp lời đọc, đặt ở {s:.1f}s")
        nb = {kk: v for kk, v in b.items() if kk not in ("at", "step_at")}
        if b.get("step_at"):   # mỗi bước sơ đồ sáng đúng lúc giọng đọc nói tới bước đó (Trọng 21/11)
            st, pos = [], (last if last >= 0 else 0)
            for phrase in b["step_at"]:
                q = [_norm(x) for x in str(phrase).split() if _norm(x)]
                hit = next((j for j in range(pos, len(ws) - len(q) + 1) if q and ws[j:j + len(q)] == q), None)
                if hit is None:
                    st.append(None)
                    continue
                pos = hit
                st.append(round(words[hit]["s"] - (s or 0), 2))
            nb["step_s"] = st
        nb = logo(sign_tone(nb))
        for side in ("left", "right"):
            if side in nb:
                nb[side] = logo(sign_tone(nb[side]))
        if "items" in nb:
            nb["items"] = [logo(x) for x in nb["items"]]
        if "cols" in nb:
            nb["cols"] = [logo(x) for x in nb["cols"]]
        if "logo" in b and nb.get("logo") is None:
            nb["logo"] = None
        if not nb.get("logo") and nb.get("type") in ("statement", "bignum", "question"):
            nb["logo"] = mention_logo(words, s, coins, nb)   # Trọng 22/11: nhắc tới dự án nào thì hiện logo dự án đó
        out.append({**nb, "s": round(max(0.0, s), 2)})
    return settle_beats(out, dur)


# Trọng 22/11: hình đang dựng dở không được biến mất (biểu đồ chưa vẽ xong đã chuyển cảnh).
# Mỗi kiểu hình có thời gian tối thiểu đủ để chạy xong hiệu ứng và để người xem đọc; "hold" kéo dài thêm.
# Tuyệt đối KHÔNG chèn khoảng lặng vào giọng đọc để giữ hình (Trọng 22/11: nghe như video bị mất tiếng).
MIN_BEAT = {"matrix": 4.5, "race": 5.5, "chart": 4.0, "versus": 3.5, "flow": 4.0, "dots": 3.0, "bignum": 2.6, "logos": 2.4,
            "statement": 2.4, "question": 2.0, "photo": 2.6}


def settle_beats(beats: list, dur: float) -> list:
    beats = sorted(beats, key=lambda b: b["s"])
    out = []
    for b in beats:
        if out:
            p = out[-1]
            need = max(MIN_BEAT.get(p.get("type"), 2.2), float(p.get("hold") or 0))
            if b["s"] < p["s"] + need:
                if b.get("type") == "question" or p["s"] + need > dur - 1.0:
                    continue   # không đủ chỗ: bỏ hình phụ, giữ hình trước cho trọn
                d = p["s"] + need - b["s"]
                b = {**b, "s": round(p["s"] + need, 2)}
                if b.get("step_s"):
                    b["step_s"] = [None if x is None else round(max(0.0, x - d), 2) for x in b["step_s"]]
        out.append(b)
    return out


ALIAS = {"GOOGL": ["google", "alphabet"], "GOOG": ["google", "alphabet"], "AMZN": ["amazon"], "META": ["meta", "facebook"],
         "MSFT": ["microsoft"], "NVDA": ["nvidia"], "AAPL": ["apple"], "TSLA": ["tesla"], "AMD": ["amd"]}
COMPANY_WORDS = sorted({a for v in ALIAS.values() for a in v} | {"intel", "oracle", "anthropic", "openai", "tsmc", "broadcom"})


def mention_logo(words: list, s: float, coins: dict, beat: dict | None = None) -> str | None:
    """Logo của dự án mà chính hình này nói tới.
    Ưu tiên chữ trên hình; hình nhắc từ 2 dự án trở lên thì không gắn logo đơn lẻ (vd CapEx của Amazon, Google, Meta, Microsoft).
    Không có tên trên hình thì chỉ xét lời đọc ngay lúc hình bật lên, không nhìn ngược về câu trước
    (lỗi 22/11: thẻ "Điều gì đã thay đổi" bị gắn logo Nvidia do câu trước nhắc Nvidia)."""
    names = {}
    for t, c in coins.items():
        if c.get("logo"):
            names[_norm(t)] = c["logo"]
            for part in str(c.get("name", "")).split():
                if len(part) >= 4 and _norm(part) not in ("protocol", "network", "finance", "token", "labs", "corporation", "inc", "platforms", "holdings"):
                    names[_norm(part)] = c["logo"]
    for t, al in ALIAS.items():
        if t in coins and coins[t].get("logo"):
            for a in al:
                names[a] = coins[t]["logo"]
    if beat:
        txt = " ".join(str(beat.get(k) or "") for k in ("text", "sub", "value", "label"))
        if sum(1 for a in COMPANY_WORDS if re.search(rf"\b{a}\b", txt.lower())) >= 2:
            return None   # nhiều công ty cùng lúc: không gắn logo một công ty
        hit = []
        for w in re.findall(r"[\w$]+", txt):
            lg = names.get(_norm(w.lstrip("$")))
            if lg and lg not in hit:
                hit.append(lg)
        if len(hit) == 1:
            return hit[0]
        if len(hit) > 1 or beat.get("type") == "statement":
            return None   # thẻ câu chữ không tự nhận logo từ lời đọc xung quanh
    near = [_norm(w["t"]) for w in words if s - 0.3 <= w["s"] <= s + 2.5]
    for w in near:
        if w in names:
            return names[w]
    return None

def project_of(s: dict, data: dict) -> dict | None:
    pj = s.get("project") or {}
    t = str(pj.get("ticker") or "").lstrip("$").upper()
    name = pj.get("name") or ""
    if not (t or name):
        return None
    c = (data.get("coins") or {}).get(t) or {}
    return {"name": name or c.get("name") or t, "ticker": t, "logo": c.get("logo"),
            "color": c.get("color") or OVERRIDE.get(t)}


def prep_public(lab: Path):
    if RD.exists():
        shutil.rmtree(RD)
    RD.mkdir(parents=True)
    for d in ["img", "logos"]:
        if (lab / d).exists():
            shutil.copytree(lab / d, RD / d)
    shutil.copytree(ROOT / "fonts", RD / "fonts")
    shutil.copy(ROOT / "logo.png", RD / "logo.png")


def run_remotion(props: dict, out: Path, frames: str = ""):
    pj = ROOT / "remotion" / "props.json"
    pj.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    env = dict(os.environ)
    if frames:
        env["ONLY_FRAMES"] = frames
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["node", "render.mjs", str(pj), str(out.resolve())], cwd=ROOT / "remotion", check=True, env=env)


def real_number(stat: str, posts: list) -> str:
    """Chỉ giữ con số CÓ THẬT trong bài gốc (không để AI bịa số). Chữ không có số (vd DCA) giữ nguyên."""
    nums = re.findall(r"\d+(?:[.,]\d+)?", stat or "")
    if not nums:
        return stat or ""
    src = " ".join(p.get("text", "") for p in posts)
    src_nums = set(x.replace(",", ".") for x in re.findall(r"\d+(?:[.,]\d+)?", src))
    return stat if all(n.replace(",", ".") in src_nums for n in nums) else ""


def _guard(props: dict):
    """Lớp chặn cuối: chữ trên hình/phụ đề không được có gạch ngang dài hay đoạn ENA 95% (Trọng cấm)."""
    import insight_lab as L
    props["scenes"] = P.nodash(props.get("scenes") or [])
    if "shortTitle" in props:
        props["shortTitle"] = P.nodash(props["shortTitle"])
    if props.get("cta"):
        props["cta"]["text"] = P.nodash(props["cta"].get("text", ""))
    chk = {k: v for k, v in props.items() if k != "data"}
    if L._banned(chk):
        raise RuntimeError("Chữ trên video còn nhắc ENA/95%/14 ngày, dừng dựng")
    return props


def render(lab: Path, out_dir: Path, voice: str | None = None, frames: str = "", shorts: bool = True) -> dict:
    cfg = V.load_cfg()
    ic = cfg.get("insight") or {}
    plan, pcm, text, data, voice = load_lab(lab, voice)
    sp_cfg = ic.get("voice_speed") or {}
    try:   # số = hệ số tốc độ; chữ khác (vd "auto") = giữ nguyên tốc độ đọc
        f = float(sp_cfg.get(voice.split(":")[0], 1.0)) if isinstance(sp_cfg, dict) else 1.0
    except (TypeError, ValueError):
        f = 1.0
    pcm = {k: speed(v, f) for k, v in pcm.items()}
    # Trọng 22/11: đoạn giáo dục quan trọng ("edu": true trong phần) đọc chậm hơn 5% cho người xem kịp hiểu, còn lại giữ nguyên
    for i, sec in enumerate(plan.get("sections") or []):
        if sec.get("edu") and f"s{i}" in pcm:
            pcm[f"s{i}"] = speed(pcm[f"s{i}"], float(ic.get("edu_speed", 0.95)))
            log(f"   Phần {i + 1} là đoạn giáo dục: đọc chậm 5%")
    orig = dict(pcm)   # video ngắn dùng giọng gốc (không có nhạc nền nên không chèn khoảng nghỉ)
    pcm, pre, brk = music_breaks(plan, pcm, text)
    audio, tl, total = build_timeline(plan, pcm, text, pre=pre)
    swell = [(sc["from"] + a, d) for sc in tl for a, d in brk.get(sc["key"], [])]
    prep_public(lab)
    V.pcm_to_wav(audio, RD / "voice.wav")
    try:
        mix_music(RD / "voice.wav", RD / "mix.wav", total, 7, swell)
        audio_file = "mix.wav"
    except Exception as ex:
        log(f"   ! nhạc lỗi: {ex}")
        audio_file = "voice.wav"
    imgs = plan.get("images", {})
    secs = plan["sections"]
    posts = plan.get("posts") or [{}]
    post = posts[0]
    brand = {"name": ic.get("brand", "Smart Penguin Insights")}
    scenes, chapters = [], []
    for sc in tl:
        k = sc["key"]
        base = {"from": sc["from"], "dur": sc["dur"], "words": sc["words"]}
        if k == "hook":
            scenes.append({**base, "type": "hook", "hook": V.en_money(plan.get("hook_screen") or plan.get("hook", "")),  # chữ trên hình đã duyệt
                           "stat": real_number(V.en_money(plan.get("hook_stat", "")), posts),
                           "label": V.en_money(plan.get("hook_label", "")) if real_number(V.en_money(plan.get("hook_stat", "")), posts) else "",
                           "images": [f"img/{x}" for x in imgs.get("intro", [])][:1],
                           "beats": beats_for(plan.get("hook_beats") or [], sc["words"], sc["dur"], data),
                           "impact": hook_impact(plan["hook_impact"], sc["words"], sc["dur"]) if plan.get("hook_impact") else None})
        elif k == "intro":
            chapters.append((sc["from"], "Mở đầu"))
            scenes.append({**base, "type": "intro", "title": V.en_money(plan.get("title", "")), "theme": plan.get("theme", ""),
                           "points": [V.en_money(s["heading"]) for s in secs][:6], "agendaLabel": P.nodash(plan.get("agenda_label", "")),
                           # review 23/11: intro_beats = thẻ đối lập ngay màn đầu (vd -$6T vs EPS mạnh nhất 4 năm) thay cho số lặp lại hook
                           "hidePost": bool(plan.get("own_source") or plan.get("intro_beats")),
                           "stat": "" if (plan.get("own_source") and plan.get("hook_beats")) or plan.get("intro_beats") else V.en_money(P.nodash(str(plan.get("thumb_stat") or plan.get("hook_stat") or "")))[:10],
                           "statLabel": P.nodash(str(plan.get("thumb_tag") or "")).upper()[:24],
                           # từ khoá tô màu trong tiêu đề = các chữ của chữ ảnh bìa (không tô bừa chữ "hội", "từ")
                           "hl": [re.sub(r"[^\w$%]", "", w.lower()) for w in str(plan.get("thumb_text") or "").split() if len(w) > 1],
                           # review 22/11: lúc chào màn hình không được trống → giữ lại thẻ so sánh của hook ở bên phải
                           "beats": [{**b, "s": 0.0} for b in beats_for(plan.get("intro_beats") or [x for x in (plan.get("hook_beats") or []) if x.get("type") in ("versus", "race", "bignum")][:1],
                                                                         sc["words"], sc["dur"], data)][:1],
                           "images": [f"img/{x}" for x in imgs.get("intro", [])][:1]})
        elif k == "outro":
            chapters.append((sc["from"], "Tóm lại"))
            scenes.append({**base, "type": "outro", "cta": P.nodash(plan.get("outro_cta", "")),
                           "points": [V.en_money(x) for x in (plan.get("outro_points") or [s["heading"] for s in secs])][:5]})
        else:
            i = int(k[1:])
            s = secs[i]
            src = [posts[j]["handle"] for j in s.get("source_ids", []) if isinstance(j, int) and j < len(posts)] or [post.get("handle", "")]
            chapters.append((sc["from"], V.en_money(s["heading"])))
            proj = project_of(s, data)
            dspec = dict(s.get("data") or {})
            if proj and dspec.get("type") in ("coin_chart", "market_heatmap", "none", None) and \
                    ((data.get("coins") or {}).get(proj["ticker"]) or {}).get("series"):
                dspec = {**dspec, "type": "coin_chart", "tickers": [proj["ticker"]]}  # có dự án → biểu đồ giá của chính dự án
            scenes.append({**base, "type": "section", "idx": i + 1, "total": len(secs), "heading": V.en_money(s["heading"]),
                           "keyStat": real_number(V.en_money(s.get("key_stat", "")), posts), "keyLabel": V.en_money(s.get("key_label", "")),
                           "bullets": [V.en_money(b) for b in (s.get("bullets") or [])][:3],
                           "quote": V.en_money(s.get("quote", "")),
                           "source": "@Trong0322" if plan.get("own_source") else (("@" + src[0]) if src[0] else ""),
                           "data": dspec or None, "project": proj,
                           "emphasis": P.nodash(str(s.get("emphasis") or "")).upper()[:32],
                           "beats": beats_for(s.get("beats") or [], sc["words"], sc["dur"], data)})
    chapters[0] = (0.0, chapters[0][1])
    pinfo = {"author": post.get("author", ""), "handle": post.get("handle", ""), "avatar": post.get("avatar"),
             "cover": post.get("cover"), "title": post.get("title", ""), "likes": post.get("likes"),
             "views": post.get("views"), "retweets": post.get("retweets")} if post else None
    if plan.get("own_source"):   # Trọng 21/11: bài trình bày như quan điểm của Trọng, hình không hiện tác giả bài gốc
        pinfo = {"author": "Trọng", "handle": "Trong0322", "avatar": "logo.png", "cover": None,
                 "title": V.en_money(plan.get("title", "")), "likes": None, "views": None, "retweets": None}
    props = {"fps": 30, "width": 1920, "height": 1080, "audio": audio_file, "duration": round(total, 3),
             "scenes": scenes, "data": data, "brand": brand, "post": pinfo}
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = lab.name
    long_path = out_dir / f"smart-penguin-{tag}-16x9.mp4"
    log(f"Dựng video dài · {total / 60:.1f} phút · giọng {voice}")
    run_remotion(_guard(props), long_path, frames)
    res = {"long": long_path, "shorts": [], "chapters": chapters, "duration": total, "voice": voice, "plan": plan, "data": data,
           "scenes": scenes}
    if not shorts or frames:
        return res
    # ---- video ngắn 9:16: mỗi insight hay nhất 1 video, cắt ở cuối câu, ≤ shorts_max_seconds ----
    mx = float(ic.get("shorts_max_seconds", 55))
    shr = plan.get("short_hooks") or {}
    # Trọng 22/11: cuối mỗi short đọc câu mời xem full video, khung kết nền trắng (InsightShort.tsx, prop cta)
    cta_pcm = orig.get("short_cta", b"")
    cta_tail = (V.gap(0.35) + cta_pcm + V.gap(1.0)) if cta_pcm else b""
    mx -= len(cta_tail) / SR / 2
    spans = plan.get("short_spans") or []
    for n, i in enumerate(plan.get("shorts", [])):
        k = f"s{i}"
        w_full = word_times(text[k], orig[k])
        full_dur = len(orig[k]) / SR / 2
        # Trọng 23/11: short lấy ĐÚNG khoảnh khắc tinh tuý (short_spans[n] = {"from": cụm đầu, "to": cụm cuối}), không cố định từ đầu phần
        sp_ = spans[n] if n < len(spans) and isinstance(spans[n], dict) else {}
        ws_ = [_norm(x["t"]) for x in w_full]

        def _hit(phrase, start=0):
            q = [_norm(x) for x in str(phrase or "").split() if _norm(x)]
            return next((j for j in range(start, len(ws_) - len(q) + 1) if q and ws_[j:j + len(q)] == q), None), len(q)
        j0, _ = _hit(sp_.get("from"))
        start = max(0.0, w_full[j0]["s"] - 0.12) if j0 is not None else 0.0
        if sp_.get("from") and j0 is None:
            log(f"   ! short {n + 1}: không thấy cụm bắt đầu '{sp_.get('from')}', lấy từ đầu phần")
        j1, ln = _hit(sp_.get("to"), j0 or 0)
        end = min(full_dur, w_full[j1 + ln - 1]["e"] + 0.25) if j1 is not None else full_dur
        if sp_.get("to") and j1 is None:
            log(f"   ! short {n + 1}: không thấy cụm kết thúc '{sp_.get('to')}', lấy tới hết phần")
        if end - start > mx:
            ends = [x["e"] for x in w_full if re.search(r"[.!?…]$", x["t"]) and start < x["e"] <= start + mx]
            end = (ends[-1] + 0.25) if ends else start + mx
        body = orig[k][int(start * SR) * 2: int(end * SR) * 2]
        a = body + (cta_tail if cta_pcm else V.gap(1.2))
        V.pcm_to_wav(a, RD / f"short{n}.wav")
        sc = next(x for x in scenes if x.get("idx") == i + 1)
        w = [{**x, "s": round(x["s"] - start, 3), "e": round(x["e"] - start, 3)} for x in w_full if x["s"] >= start - 0.05 and x["s"] < end]
        bts = beats_for(plan["sections"][i].get("beats") or [], w_full, full_dur, data)   # gắn hình theo cả phần rồi dời về mốc short
        cur = [b for b in bts if b["s"] <= start + 0.2]
        if cur:   # hình đang chạy lúc short bắt đầu: dời về giây 0, các bước sơ đồ dời theo
            c0 = dict(cur[-1])
            d = start - c0["s"]
            if c0.get("step_s"):
                c0["step_s"] = [None if x is None else round(max(0.0, x - d), 2) for x in c0["step_s"]]
            cur = [c0]
        bts = ([{**cur[-1], "s": 0.0}] if cur else []) + [{**b, "s": round(b["s"] - start, 3)} for b in bts if start + 0.2 < b["s"] < end]
        log(f"   Short {n + 1}: phần {i + 1}, giây {start:.1f} đến {end:.1f}")
        sprops = {"fps": 30, "width": 1080, "height": 1920, "audio": f"short{n}.wav", "duration": round(len(a) / SR / 2, 3),
                  "scenes": [{**sc, "from": 0, "dur": round(len(a) / SR / 2, 3), "words": w, "beats": bts}],
                  "data": data, "brand": brand, "post": pinfo,
                  "shortTitle": V.en_money(str(plan.get("short_title") or shr.get(str(i)) or shr.get(i) or sc["heading"]))}
        if plan.get("news"):   # Trọng 24/11: tin nóng ghi nguồn tin thật thay vì "Source: @Trong0322"
            sprops["sourceLabel"] = P.nodash(str(plan.get("source_label") or (plan.get("source_post") or {}).get("author") or ""))[:60]
        if cta_pcm:
            sprops["cta"] = {"text": V.en_money(text.get("short_cta", "")), "from": round(len(body) / SR / 2 + 0.2, 3)}
        try:   # Trọng 22/11: giây đầu của short chính là ảnh bìa (TikTok/Reels lấy khung đầu làm bìa, người lướt thấy ngay số liệu)
            import short_covers as SC
            lg = {kk: v.get("logo") for kk, v in (data.get("coins") or {}).items()}
            sprops["cover"] = {kk: v for kk, v in SC.props_for(plan, i, sprops["shortTitle"], lg).items() if kk not in ("comp", "width", "height")}
        except Exception as ex:
            log(f"   ! khung bìa đầu short lỗi: {ex}")
        sp = out_dir / f"smart-penguin-{tag}-short{n + 1}-9x16.mp4"
        log(f"Dựng video ngắn {n + 1} · {len(a) / SR / 2:.0f}s")
        run_remotion(_guard(sprops), sp)
        res["shorts"].append({"path": sp, "section": i, "title": sprops["shortTitle"]})
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", required=True)
    ap.add_argument("--out", default="out")
    ap.add_argument("--voice", default="")
    ap.add_argument("--frames", default="", help="chỉ xuất ảnh khung hình ở các giây này (kiểm tra nhanh)")
    ap.add_argument("--no-shorts", action="store_true")
    a = ap.parse_args()
    r = render(Path(a.lab), Path(a.out), a.voice or None, a.frames, not a.no_shorts)
    print(json.dumps({"long": str(r["long"]), "shorts": [str(s["path"]) for s in r["shorts"]]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
