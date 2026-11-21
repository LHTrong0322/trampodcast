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


def build_timeline(plan, pcm, text, gap=0.35):
    """Ghép audio các đoạn (nghỉ ngắn giữa đoạn để giữ nhịp) + lập danh sách cảnh (giây)."""
    secs = plan["sections"]
    order = (["hook"] if "hook" in pcm else []) + ["intro"] + [f"s{k}" for k in range(len(secs))] + ["outro"]
    audio, scenes, t = b"", [], 0.0
    for key in order:
        a = pcm[key] + V.gap(gap if key != "outro" else 2.6)
        dur = len(a) / SR / 2
        scenes.append({"key": key, "from": round(t, 3), "dur": round(dur, 3), "words": word_times(text[key], pcm[key])})
        audio += a
        t += dur
    return audio, scenes, t


def mix_music(voice_wav: Path, out_wav: Path, seconds: float, seed: int):
    """Nhạc nền tự nhỏ đi khi có giọng, chuẩn âm lượng YouTube."""
    raw = MU.make_music(seconds + 1, seed)
    tmp = out_wav.with_suffix(".pcm")
    tmp.write_bytes(raw.tobytes() if hasattr(raw, "tobytes") else raw)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(voice_wav), "-f", "s16le", "-ar", str(SR), "-ac", "1",
                    "-i", str(tmp), "-filter_complex",
                    "[1:a]lowpass=f=3200,volume=0.2[m];[0:a]asplit=2[v1][v2];"
                    "[m][v1]sidechaincompress=threshold=0.015:ratio=6:attack=20:release=450[md];"
                    "[v2][md]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
                    "-map", "[a]", "-ar", "48000", str(out_wav)], check=True)
    tmp.unlink()



def _norm(w: str) -> str:
    return re.sub(r"[^\w%$/]", "", w.lower())


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
        nb = logo(nb)
        for side in ("left", "right"):
            if side in nb:
                nb[side] = logo(nb[side])
        if "items" in nb:
            nb["items"] = [logo(x) for x in nb["items"]]
        if "logo" in b and nb.get("logo") is None:
            nb["logo"] = None
        out.append({**nb, "s": round(max(0.0, s), 2)})
    return out

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
    audio, tl, total = build_timeline(plan, pcm, text)
    prep_public(lab)
    V.pcm_to_wav(audio, RD / "voice.wav")
    try:
        mix_music(RD / "voice.wav", RD / "mix.wav", total, 7)
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
                           "beats": beats_for(plan.get("hook_beats") or [], sc["words"], sc["dur"], data)})
        elif k == "intro":
            chapters.append((sc["from"], "Mở đầu"))
            scenes.append({**base, "type": "intro", "title": V.en_money(plan.get("title", "")), "theme": plan.get("theme", ""),
                           "points": [V.en_money(s["heading"]) for s in secs][:6], "agendaLabel": P.nodash(plan.get("agenda_label", "")),
                           "images": [f"img/{x}" for x in imgs.get("intro", [])][:1]})
        elif k == "outro":
            chapters.append((sc["from"], "Tóm lại"))
            scenes.append({**base, "type": "outro", "points": [V.en_money(s["heading"]) for s in secs][:5]})
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
    res = {"long": long_path, "shorts": [], "chapters": chapters, "duration": total, "voice": voice, "plan": plan,
           "scenes": scenes}
    if not shorts or frames:
        return res
    # ---- video ngắn 9:16: mỗi insight hay nhất 1 video, cắt ở cuối câu, ≤ shorts_max_seconds ----
    mx = float(ic.get("shorts_max_seconds", 55))
    shr = plan.get("short_hooks") or {}
    for n, i in enumerate(plan.get("shorts", [])):
        k = f"s{i}"
        w = word_times(text[k], pcm[k])
        end = len(pcm[k]) / SR / 2
        if end > mx:
            ends = [x["e"] for x in w if re.search(r"[.!?…]$", x["t"]) and x["e"] <= mx]
            end = (ends[-1] + 0.25) if ends else mx
        a = pcm[k][: int(end * SR) * 2] + V.gap(1.2)
        V.pcm_to_wav(a, RD / f"short{n}.wav")
        sc = next(x for x in scenes if x.get("idx") == i + 1)
        sprops = {"fps": 30, "width": 1080, "height": 1920, "audio": f"short{n}.wav", "duration": round(len(a) / SR / 2, 3),
                  "scenes": [{**sc, "from": 0, "dur": round(len(a) / SR / 2, 3), "words": [x for x in w if x["s"] < end]}],
                  "data": data, "brand": brand, "post": pinfo,
                  "shortTitle": V.en_money(str(shr.get(str(i)) or shr.get(i) or sc["heading"]))}
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
