#!/usr/bin/env python3
"""
Dựng video Insight từ "nguyên liệu" LAB (insight_lab.py) theo nhiều kiểu:

  python insight_render.py remotion --lab lab/<tag> --voice "vieneu:Hải Đăng" --mode motion
  python insight_render.py remotion --lab lab/<tag> --voice "vieneu:Hải Đăng" --mode data
  python insight_render.py classic  --lab lab/<tag> --voice "gemini:Ludo"

remotion: dựng bằng Remotion (React) — motion graphics; mode=data: ưu tiên hình dữ liệu thật thay ảnh.
classic : bộ dựng Python (motion.py) đã nâng cấp.
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


def load_lab(lab: Path, voice: str):
    plan = json.loads((lab / "plan.json").read_text(encoding="utf-8"))
    vdir = plan["voices"].get(voice)
    if not vdir:
        raise SystemExit(f"Không có audio cho giọng {voice}")
    pcm = {p["key"]: V.file_to_pcm(lab / "audio" / vdir / f"{i:02d}.wav") for i, p in enumerate(plan["parts"])}
    text = {p["key"]: p["text"] for p in plan["parts"]}
    data = json.loads((lab / "data.json").read_text(encoding="utf-8")) if (lab / "data.json").exists() else {}
    return plan, pcm, text, data


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


def build_timeline(plan, pcm, text, gap=0.55):
    """Ghép audio các đoạn + lập danh sách cảnh (giây)."""
    secs = plan["sections"]
    order = (["hook"] if "hook" in pcm else []) + ["intro"] + [f"s{k}" for k in range(len(secs))] + ["outro"]
    audio, scenes, t = b"", [], 0.0
    for key in order:
        a = pcm[key] + V.gap(gap if key != "outro" else 2.8)
        dur = len(a) / SR / 2
        scenes.append({"key": key, "from": round(t, 3), "dur": round(dur, 3), "words": word_times(text[key], pcm[key])})
        audio += a
        t += dur
    return audio, scenes, t


def music_track(seconds: float, path: Path, seed: int):
    raw = MU.make_music(seconds + 1, seed)
    tmp = path.with_suffix(".pcm")
    tmp.write_bytes(raw.tobytes() if hasattr(raw, "tobytes") else raw)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", str(tmp),
                    "-af", "lowpass=f=3200", str(path)], check=True)
    tmp.unlink()


def remotion(lab: Path, voice: str, mode: str, out: Path) -> Path:
    plan, pcm, text, data = load_lab(lab, voice)
    audio, tl, total = build_timeline(plan, pcm, text)
    rd = ROOT / "remotion" / "public"
    if rd.exists():
        shutil.rmtree(rd)
    rd.mkdir(parents=True)
    V.pcm_to_wav(audio, rd / "voice.wav")
    for d in ["img", "logos"]:
        if (lab / d).exists():
            shutil.copytree(lab / d, rd / d)
    shutil.copytree(ROOT / "fonts", rd / "fonts")
    shutil.copy(ROOT / "logo.png", rd / "logo.png")
    imgs = plan.get("images", {})
    secs = plan["sections"]
    post = (plan.get("posts") or [{}])[0]
    scenes = []
    for sc in tl:
        k = sc["key"]
        base = {"from": sc["from"], "dur": sc["dur"], "words": sc["words"]}
        if k == "hook":
            scenes.append({**base, "type": "hook", "hook": V.en_money(plan.get("hook", "")),
                           "stat": V.en_money(plan.get("hook_stat", "")), "label": V.en_money(plan.get("hook_label", "")),
                           "images": [f"img/{x}" for x in imgs.get("intro", [])]})
        elif k == "intro":
            scenes.append({**base, "type": "intro", "title": V.en_money(plan.get("title", "")), "theme": plan.get("theme", ""),
                           "points": [V.en_money(s["heading"]) for s in secs][:6],
                           "images": [f"img/{x}" for x in imgs.get("intro", [])[1:]]})
        elif k == "outro":
            scenes.append({**base, "type": "outro", "points": [s["heading"] for s in secs][:4]})
        else:
            i = int(k[1:])
            s = secs[i]
            src = [plan["posts"][j]["handle"] for j in s.get("source_ids", []) if isinstance(j, int) and j < len(plan["posts"])]
            scenes.append({**base, "type": "section", "idx": i + 1, "total": len(secs), "heading": V.en_money(s["heading"]),
                           "keyStat": V.en_money(s.get("key_stat", "")), "keyLabel": V.en_money(s.get("key_label", "")),
                           "bullets": [V.en_money(b) for b in (s.get("bullets") or [])][:3],
                           "quote": V.en_money(s.get("quote", "")), "source": ("@" + src[0]) if src else "",
                           "data": s.get("data"), "images": [f"img/{x}" for x in imgs.get(f"s{i}", [])]})
    music = None
    try:  # trộn sẵn nhạc nền (tự nhỏ đi khi có giọng) vào 1 file âm thanh
        music_track(total, rd / "music.wav", 7)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(rd / "voice.wav"), "-i", str(rd / "music.wav"),
                        "-filter_complex",
                        "[0:a]asplit=2[v1][v2];[1:a]volume=0.22[m];"
                        "[m][v1]sidechaincompress=threshold=0.015:ratio=6:attack=20:release=450[md];"
                        "[v2][md]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
                        "-map", "[a]", "-ar", "48000", str(rd / "mix.wav")], check=True)
        (rd / "music.wav").unlink()
    except Exception as ex:
        log(f"   ! nhạc lỗi: {ex}")
    props = {"fps": 30, "width": 1920, "height": 1080, "audio": "mix.wav" if (rd / "mix.wav").exists() else "voice.wav", "music": music, "duration": round(total, 3),
             "scenes": scenes, "data": data, "mode": mode,
             "brand": {"name": (V.load_cfg().get("insight") or {}).get("brand", "Smart Penguin Insights")},
             "post": {"author": post.get("author", ""), "handle": post.get("handle", ""), "avatar": post.get("avatar"),
                      "cover": post.get("cover"), "title": post.get("title", ""), "likes": post.get("likes"),
                      "views": post.get("views"), "retweets": post.get("retweets")} if post else None}
    pj = ROOT / "remotion" / "props.json"
    pj.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)
    log(f"Remotion · {mode} · {total / 60:.1f} phút → {out}")
    subprocess.run(["node", "render.mjs", str(pj), str(out.resolve())], cwd=ROOT / "remotion", check=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("engine", choices=["remotion", "classic"])
    ap.add_argument("--lab", required=True)
    ap.add_argument("--voice", required=True)
    ap.add_argument("--mode", default="motion")
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", default="", help="chỉ xuất ảnh khung hình ở các giây này (kiểm tra nhanh)")
    a = ap.parse_args()
    if a.frames:
        os.environ["ONLY_FRAMES"] = a.frames
    if a.engine == "remotion":
        remotion(Path(a.lab), a.voice, a.mode, Path(a.out))
    else:
        import insight_classic
        insight_classic.render(Path(a.lab), a.voice, Path(a.out))


if __name__ == "__main__":
    main()
