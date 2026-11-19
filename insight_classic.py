"""Bộ dựng 'classic' (Python, motion.py) cho video Insight từ nguyên liệu LAB — bản Claude nâng cấp:
thẻ bài X ở phần mở đầu, ý chính hiện dần theo lời đọc, biểu đồ giá thật của coin được nhắc, ảnh theo từng ý."""
from __future__ import annotations

import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

import motion as M
import music as MU
import podcast as P
import video as V
import insight_render as R

log = P.log
SR = V.SR


def _imgs(lab: Path, names: list[str], credits: dict) -> list:
    out = []
    for n in names:
        try:
            out.append((Image.open(lab / "img" / n).convert("RGB"), credits.get(n, "")))
        except Exception:
            pass
    return out


def post_card(lab: Path, post: dict) -> Image.Image:
    W, H = 720, 410 if post.get("cover") else 230
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, W - 1, H - 1], 30, fill=255)
    base = Image.new("RGBA", (W, H), (22, 19, 36, 245))
    y = 0
    if post.get("cover"):
        from PIL import ImageOps
        cv = ImageOps.fit(Image.open(lab / post["cover"]).convert("RGB"), (W, 180))
        base.paste(cv, (0, 0))
        y = 180
    d = ImageDraw.Draw(base)
    if post.get("avatar"):
        av = Image.open(lab / post["avatar"]).convert("RGB").resize((70, 70))
        am = Image.new("L", (70, 70), 0)
        ImageDraw.Draw(am).ellipse([0, 0, 69, 69], fill=255)
        base.paste(av, (28, y + 26), am)
    d.text((114, y + 28), post.get("author", ""), font=V.font("ExtraBold", 30), fill=V.CREAM)
    d.text((114, y + 64), "@" + post.get("handle", ""), font=V.font("SemiBold", 24), fill=V.MUTED)
    d.text((W - 60, y + 30), "X", font=V.font("ExtraBold", 40), fill=V.CREAM)
    if post.get("title"):
        d.text((28, y + 122), post["title"][:44], font=V.font("ExtraBold", 34), fill=V.CREAM)
    card.paste(base, (0, 0), m)
    ImageDraw.Draw(card).rounded_rectangle([0, 0, W - 1, H - 1], 30, outline=(123, 92, 255, 230), width=3)
    return card


def render(lab: Path, voice: str, out: Path) -> Path:
    plan, pcm, text, data = R.load_lab(lab, voice)
    cfg = V.load_cfg()
    ic = cfg.get("insight") or {}
    V.BRAND.update(name=ic.get("brand", "Smart Penguin Insights").upper(), title_tag="INSIGHT CRYPTO",
                   outro_line=ic.get("outro_line", "Đăng ký kênh để nhận insight crypto"))
    V.CAT_COLORS.setdefault("Insight", (123, 92, 255))
    cr = plan.get("image_credits", {})
    imgs = plan.get("images", {})
    secs = plan["sections"]
    post = (plan.get("posts") or [{}])[0]
    theme = plan.get("theme", "Insight")
    T = 0.6
    scenes = []
    intro_imgs = _imgs(lab, imgs.get("intro", []), cr)
    if "hook" in pcm:
        hd = len(pcm["hook"]) / SR / 2 + 0.35
        scenes.append({"dur": hd, "pcm": pcm["hook"] + V.gap(0.35), "wipe": False,
                       "draw": V.scene_hook(V.en_money(plan.get("hook", "")), V.en_money(plan.get("hook_stat", "")),
                                            V.en_money(plan.get("hook_label", "")), hd, intro_imgs)})
    idur = len(pcm["intro"]) / SR / 2 + T
    base_intro = V.scene_title(V.en_money(plan.get("title", theme)), theme, "", idur, intro_imgs)
    card = post_card(lab, post) if post else None
    card_ly = M.Layer(card, 1120, 190, "slide_left", 0.8, 0.8) if card else None

    def intro_draw(c, t, ctx, _b=base_intro, _ly=card_ly):
        _b(c, t, ctx)
        if _ly:
            _ly.draw(c, t)
    scenes.append({"dur": idur, "pcm": pcm["intro"] + V.gap(T), "wipe": "hook" in pcm, "draw": intro_draw})
    wl = f"Insight · {theme}"
    coins = (data or {}).get("coins", {})
    for k, s in enumerate(secs):
        p_ = pcm[f"s{k}"]
        d_ = s.get("data") or {}
        cc = None
        if d_.get("type") == "coin_chart":
            t_ = str((d_.get("tickers") or [""])[0]).lstrip("$").upper()
            if t_ in coins:
                cc = (t_, coins[t_]["series"][-28:])  # ≈ 7 ngày gần nhất (khớp nhãn "7 ngày")
        item = {"headline": V.en_money(s["heading"]), "key_stat": V.en_money(s.get("key_stat", "")),
                "key_label": V.en_money(s.get("key_label", "")), "narration": text[f"s{k}"],
                "sub_text": V.en_money(text[f"s{k}"]), "category": "Insight", "tickers": [], "is_update": False,
                "date": "2026-01-01T00:00:00", "date_text": "theo @" + post.get("handle", ""), "pcm": p_,
                "speech_dur": len(p_) / SR / 2, "coin_chart": cc}
        a_ = p_ + V.gap(T)
        dur = len(a_) / SR / 2
        base = V.scene_story_h(item, k + 1, len(secs), wl, dur, _imgs(lab, imgs.get(f"s{k}", []), cr), 4.0)
        # ý chính hiện dần ở cột trái, dưới tiêu đề
        bl = []
        for j, b in enumerate((s.get("bullets") or [])[:3]):
            ti = V.chip_img(f"{j + 1}  {V.en_money(b)}", (60, 46, 120), V.font("Bold", 34))
            bl.append(M.Layer(ti, 120, 640 + j * 82, "slide_left", 1.5 + dur * 0.6 * j / 3, 0.5))

        def draw(c, t, ctx, _b=base, _bl=bl):
            _b(c, t, ctx)
            for ly in _bl:
                ly.draw(c, t)
        scenes.append({"dur": dur, "pcm": a_, "draw": draw})
    o_ = pcm["outro"] + V.gap(2.5)
    scenes.append({"dur": len(o_) / SR / 2, "pcm": o_, "draw": V.scene_outro()})
    for sc in scenes:
        n = int(round(sc["dur"] * M.FPS))
        sc["pcm"] = (sc["pcm"] + V.gap(1))[: int(n / M.FPS * SR) * 2]
        sc["dur"] = n / M.FPS
    total = sum(s_["dur"] for s_ in scenes)
    log(f"Classic · {total / 60:.1f} phút → {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    return M.render(scenes, 1920, 1080, out, Path(tempfile.mkdtemp()), log=log, watermark=V.watermark_layer(False),
                    music_pcm=MU.make_music(total + 1, 11), music_vol=0.22)
