"""Smart Penguin Insights: hậu kỳ + kiểm tra thông số xuất bản theo nền tảng (YouTube, Shorts, TikTok, Reels).

Chạy SAU khi Remotion dựng xong, TRƯỚC khi tạo GitHub Release (gọi từ insight_publish.publish):
  - Video dài 16:9: nâng lên 2560x1440 (1440p) để YouTube cấp codec VP9 chất lượng cao, H.264 High, yuv420p,
    BT.709, GOP đóng 15 khung (nửa fps), moov ở đầu file (faststart), AAC 48kHz stereo, độ lớn -14 LUFS.
  - Video ngắn 9:16: 1080x1920, 30fps, cùng chuẩn mã hoá, 1 file dùng chung cho Shorts / TikTok / Reels.
  - Ảnh bìa YouTube 1280x720 dưới 2MB; ảnh bìa dọc 1080x1920 cho từng short.
  - Kiểm tra tự động bằng ffprobe; sai thông số → báo lỗi rõ ràng (SpecError).

Cấu hình: sources.yaml → insight.publish (thông số) và insight.safe_zones (vùng an toàn khung dọc).

Dòng lệnh:
  python platform_export.py selftest              # tự tạo video mẫu, xử lý, kiểm tra (chạy trên GitHub trước khi dựng)
  python platform_export.py check FILE [FILE...]  # chỉ kiểm tra file có sẵn (.mp4 dài/ngắn tự nhận theo chiều)
  python platform_export.py fix FILE [FILE...]    # xử lý lại tại chỗ rồi kiểm tra
"""
from __future__ import annotations

import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

DEFAULTS = {
    "long": {"width": 2560, "height": 1440, "fps": 30, "crf": 16, "maxrate": "24M", "bufsize": "48M",
             "preset": "fast", "fallback_height": 1080},
    "short": {"width": 1080, "height": 1920, "fps": 30, "crf": 17, "maxrate": "12M", "bufsize": "24M",
              "preset": "medium", "warn_seconds": 60, "max_seconds": 180},
    "audio": {"sample_rate": 48000, "channels": 2, "bitrate": "384k", "lufs": -14.0, "true_peak": -1.0,
              "lra": 11.0, "lufs_tolerance": 1.5},
    "thumb": {"width": 1280, "height": 720, "max_bytes": 2_000_000},
    "vertical_cover": True,
    "vertical_cover_at": 1.2,
    "strict": True,
}


class SpecError(RuntimeError):
    """File đầu ra sai thông số nền tảng."""


def _log(*a):
    print("[platform_export]", *a, flush=True)


def load_cfg() -> dict:
    cfg = json.loads(json.dumps(DEFAULTS))
    try:
        import yaml
        ic = (yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8")) or {}).get("insight") or {}
        pub = ic.get("publish") or {}
        for k, v in pub.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    except Exception as e:  # thiếu yaml hoặc file lỗi → dùng mặc định
        _log("dùng thông số mặc định:", e)
    return cfg


# ---------------------------------------------------------------- ffprobe / ffmpeg tiện ích
def _run(cmd: list[str], timeout: float | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)


def probe(path: Path) -> dict:
    r = _run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)])
    if r.returncode:
        raise SpecError(f"{path.name}: ffprobe không đọc được file ({r.stderr.strip()[:200]})")
    return json.loads(r.stdout)


def _streams(info: dict, kind: str) -> list[dict]:
    return [s for s in info.get("streams", []) if s.get("codec_type") == kind]


def _fps(s: dict) -> float:
    n, _, d = (s.get("avg_frame_rate") or s.get("r_frame_rate") or "0/1").partition("/")
    try:
        return float(n) / float(d or 1)
    except (ValueError, ZeroDivisionError):
        return 0.0


def moov_first(path: Path) -> bool:
    """True nếu hộp 'moov' (mục lục) nằm trước 'mdat' (dữ liệu) → xem/tải lên được ngay khi đang tải (faststart)."""
    with open(path, "rb") as f:
        while True:
            head = f.read(8)
            if len(head) < 8:
                return False
            size, typ = struct.unpack(">I4s", head)
            if typ == b"moov":
                return True
            if typ == b"mdat":
                return False
            if size == 1:
                size = struct.unpack(">Q", f.read(8))[0]
                f.seek(size - 16, 1)
            elif size == 0:
                return False
            else:
                f.seek(size - 8, 1)


def loudness(path: Path) -> dict:
    """Đo độ lớn (EBU R128): I = LUFS tích hợp, TP = đỉnh thật (dBTP), LRA = biên độ."""
    r = _run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af",
              "loudnorm=I=-14:TP=-1:LRA=11:print_format=json", "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        raise SpecError(f"{path.name}: không đo được độ lớn âm thanh (loudnorm)")
    return json.loads(m.group(0))


def max_keyframe_gap(path: Path, fps: float, seconds: float = 20) -> int:
    """Khoảng cách lớn nhất giữa 2 khung khoá (keyframe) trong N giây đầu, tính bằng số khung hình."""
    r = _run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-skip_frame", "nokey", "-read_intervals",
              f"%+{seconds}", "-show_entries", "frame=pts_time,best_effort_timestamp_time", "-of", "csv=p=0", str(path)])
    ts = []
    for line in r.stdout.split():
        for x in line.split(","):
            try:
                ts.append(float(x))
                break
            except ValueError:
                continue
    ts = sorted(set(ts))
    if len(ts) < 2:
        return 0
    return round(max(b - a for a, b in zip(ts, ts[1:])) * fps)


# ---------------------------------------------------------------- xử lý
def _vcodec_args(spec: dict, fps: int) -> list[str]:
    g = max(1, fps // 2)  # GOP = nửa fps (YouTube khuyên)
    return ["-c:v", "libx264", "-profile:v", "high", "-preset", str(spec["preset"]), "-crf", str(spec["crf"]),
            "-maxrate", str(spec["maxrate"]), "-bufsize", str(spec["bufsize"]), "-pix_fmt", "yuv420p",
            "-g", str(g), "-keyint_min", str(g), "-sc_threshold", "0", "-bf", "2", "-flags", "+cgop",
            "-x264-params", "open-gop=0:colorprim=bt709:transfer=bt709:colormatrix=bt709",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
            "-r", str(fps)]


def _audio_args(a: dict, meas: dict | None) -> list[str]:
    if meas and all(k in meas for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")) \
            and meas["input_i"] not in ("-inf", "inf"):
        ln = (f"loudnorm=I={a['lufs']}:TP={a['true_peak']}:LRA={a['lra']}:measured_I={meas['input_i']}"
              f":measured_TP={meas['input_tp']}:measured_LRA={meas['input_lra']}"
              f":measured_thresh={meas['input_thresh']}:offset={meas['target_offset']}:linear=true")
    else:
        ln = f"loudnorm=I={a['lufs']}:TP={a['true_peak']}:LRA={a['lra']}"
    # loudnorm nội bộ chạy 192kHz → ép lại 48kHz
    return ["-af", f"{ln},aresample={a['sample_rate']}", "-c:a", "aac", "-b:a", str(a["bitrate"]),
            "-ar", str(a["sample_rate"]), "-ac", str(a["channels"])]


def _color_filter(v: dict) -> str:
    """Remotion mặc định xuất ma trận màu BT.601 không gắn nhãn → đổi sang BT.709 cho đúng màu trên YouTube/TikTok."""
    cs = (v.get("color_space") or "").lower()
    src = "bt709" if cs in ("bt709",) else "bt601"
    rng = "pc" if (v.get("pix_fmt") or "").startswith("yuvj") or v.get("color_range") in ("pc", "jpeg") else "tv"
    return f"in_color_matrix={src}:out_color_matrix=bt709:in_range={rng}:out_range=tv"


def process_video(path: Path, kind: str, cfg: dict | None = None) -> Path:
    """Mã hoá lại tại chỗ theo chuẩn nền tảng. kind = 'long' (16:9) hoặc 'short' (9:16)."""
    cfg = cfg or load_cfg()
    spec, a = cfg[kind], cfg["audio"]
    info = probe(path)
    v = (_streams(info, "video") or [None])[0]
    if not v:
        raise SpecError(f"{path.name}: không có hình")
    has_audio = bool(_streams(info, "audio"))
    fps = int(spec["fps"])
    W, H = int(spec["width"]), int(spec["height"])
    vf = f"scale={W}:{H}:flags=lanczos:{_color_filter(v)},setsar=1,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv"
    tmp = path.with_name(path.stem + ".platform.tmp.mp4")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(path)]
    if has_audio:
        meas = None
        try:
            meas = loudness(path)
        except SpecError as e:
            _log("bỏ qua đo trước:", e)
        cmd += ["-map", "0:v:0", "-map", "0:a:0", *_audio_args(a, meas)]
    else:
        # nền tảng đều cần track âm thanh: thêm im lặng
        cmd += ["-f", "lavfi", "-i", f"anullsrc=r={a['sample_rate']}:cl=stereo", "-map", "0:v:0", "-map", "1:a:0",
                "-shortest", "-c:a", "aac", "-b:a", str(a["bitrate"]), "-ar", str(a["sample_rate"]), "-ac", "2"]
    cmd += ["-vf", vf, *_vcodec_args(spec, fps), "-movflags", "+faststart", "-map_metadata", "-1", str(tmp)]
    _log(f"mã hoá {path.name} → {W}x{H}@{fps}")
    r = _run(cmd)
    if r.returncode or not tmp.exists():
        tmp.unlink(missing_ok=True)
        raise SpecError(f"{path.name}: ffmpeg mã hoá lỗi: {r.stderr.strip()[-400:]}")
    tmp.replace(path)
    return path


def process_thumb(path: Path, cfg: dict | None = None) -> Path:
    """Ảnh bìa YouTube: đúng 1280x720, dưới 2MB (PNG quá nặng → JPEG)."""
    from PIL import Image
    cfg = cfg or load_cfg()
    t = cfg["thumb"]
    W, H, mx = int(t["width"]), int(t["height"]), int(t["max_bytes"])
    im = Image.open(path).convert("RGB")
    if im.size != (W, H):
        # cắt giữa đúng 16:9 rồi thu nhỏ
        r = W / H
        w, h = im.size
        if abs(w / h - r) > 0.01:
            if w / h > r:
                nw = round(h * r); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
            else:
                nh = round(w / r); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
        im = im.resize((W, H), Image.LANCZOS)
    if path.suffix.lower() == ".png":
        im.save(path, optimize=True)
        if path.stat().st_size <= mx:
            return path
        jpg = path.with_suffix(".jpg")
        path.unlink(missing_ok=True)
        path = jpg
    for q in (92, 88, 84, 80, 75, 70):
        im.save(path, "JPEG", quality=q, optimize=True, progressive=True)
        if path.stat().st_size <= mx:
            break
    return path


def vertical_cover(short: Path, cfg: dict | None = None) -> Path | None:
    """Ảnh bìa dọc 1080x1920 (khung hook đầu short) để chọn làm cover TikTok/Reels/Shorts."""
    cfg = cfg or load_cfg()
    out = short.with_name(f"cover-9x16-{short.stem}.jpg")
    r = _run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(cfg.get("vertical_cover_at", 1.2)), "-i", str(short),
              "-frames:v", "1", "-vf", "scale=1080:1920:flags=lanczos", "-q:v", "2", str(out)])
    return out if r.returncode == 0 and out.exists() else None


# ---------------------------------------------------------------- kiểm tra
def check_video(path: Path, kind: str, cfg: dict | None = None) -> list[str]:
    """Trả về danh sách lỗi (rỗng = đạt). Cảnh báo nhẹ chỉ in ra."""
    cfg = cfg or load_cfg()
    spec, a = cfg[kind], cfg["audio"]
    errs: list[str] = []
    info = probe(path)
    v = (_streams(info, "video") or [{}])[0]
    au = (_streams(info, "audio") or [{}])[0]
    W, H, fps = int(spec["width"]), int(spec["height"]), int(spec["fps"])
    okH = {H} | ({int(spec["fallback_height"])} if kind == "long" and spec.get("fallback_height") else set())
    size = (v.get("width"), v.get("height"))
    if kind == "long":
        if v.get("height") not in okH or v.get("width") != round(v.get("height", 0) * 16 / 9):
            errs.append(f"kích thước {size}, cần {W}x{H} (16:9)")
    elif size != (W, H):
        errs.append(f"kích thước {size}, cần {W}x{H} (9:16)")
    if v.get("codec_name") != "h264":
        errs.append(f"codec hình {v.get('codec_name')}, cần h264")
    if (v.get("profile") or "").lower() != "high":
        errs.append(f"profile {v.get('profile')}, cần High")
    if v.get("pix_fmt") != "yuv420p":
        errs.append(f"pix_fmt {v.get('pix_fmt')}, cần yuv420p (4:2:0)")
    if abs(_fps(v) - fps) > 0.05:
        errs.append(f"fps {_fps(v):.2f}, cần {fps}")
    if (v.get("color_primaries"), v.get("color_transfer"), v.get("color_space")) != ("bt709",) * 3:
        errs.append(f"màu {v.get('color_primaries')}/{v.get('color_transfer')}/{v.get('color_space')}, cần BT.709")
    gap = max_keyframe_gap(path, fps)
    if gap > fps:
        errs.append(f"khoảng cách keyframe {gap} khung, cần ≤ {fps // 2} (GOP nửa fps)")
    if not au:
        errs.append("không có âm thanh")
    else:
        if au.get("codec_name") != "aac":
            errs.append(f"codec âm thanh {au.get('codec_name')}, cần AAC")
        if int(au.get("sample_rate") or 0) != int(a["sample_rate"]):
            errs.append(f"sample rate {au.get('sample_rate')}, cần {a['sample_rate']}")
        if int(au.get("channels") or 0) != int(a["channels"]):
            errs.append(f"{au.get('channels')} kênh, cần stereo")
        ln = loudness(path)
        try:
            li = float(ln["input_i"]); tp = float(ln["input_tp"])
        except ValueError:
            li, tp = -99.0, -99.0
        if abs(li - float(a["lufs"])) > float(a["lufs_tolerance"]):
            errs.append(f"độ lớn {li:.1f} LUFS, cần {a['lufs']} ± {a['lufs_tolerance']}")
        if tp > float(a["true_peak"]) + 0.5:
            errs.append(f"đỉnh thật {tp:.1f} dBTP, cần ≤ {a['true_peak']}")
        _log(f"{path.name}: {li:.1f} LUFS, đỉnh {tp:.1f} dBTP")
    if not moov_first(path):
        errs.append("moov không nằm đầu file (thiếu faststart)")
    dur = float(info.get("format", {}).get("duration") or 0)
    if kind == "short":
        if dur > float(spec["max_seconds"]):
            errs.append(f"dài {dur:.0f}s > {spec['max_seconds']}s: YouTube không xếp vào Shorts")
        elif dur > float(spec["warn_seconds"]):
            _log(f"CẢNH BÁO {path.name}: dài {dur:.0f}s > 60s (Shorts trên 1 phút dễ bị chặn nếu dính bản quyền nhạc)")
    if kind == "long" and v.get("height") != H:
        _log(f"CẢNH BÁO {path.name}: đang là {v.get('height')}p, chưa phải {H}p → YouTube có thể chỉ cấp codec AVC1")
    return [f"{path.name}: {e}" for e in errs]


def check_thumb(path: Path, cfg: dict | None = None) -> list[str]:
    from PIL import Image
    cfg = cfg or load_cfg()
    t = cfg["thumb"]
    errs = []
    with Image.open(path) as im:
        if im.size != (int(t["width"]), int(t["height"])):
            errs.append(f"ảnh bìa {im.size}, cần {t['width']}x{t['height']}")
    if path.stat().st_size > int(t["max_bytes"]):
        errs.append(f"ảnh bìa nặng {path.stat().st_size / 1e6:.2f}MB > 2MB")
    return [f"{path.name}: {e}" for e in errs]


def kind_of(path: Path) -> str:
    v = (_streams(probe(path), "video") or [{}])[0]
    return "short" if (v.get("height") or 0) > (v.get("width") or 0) else "long"


# ---------------------------------------------------------------- điểm gọi chính
def prepare(res: dict, thumb: Path | None, log=_log) -> tuple[dict, Path | None, list[Path]]:
    """Gọi trong insight_publish.publish trước khi tạo Release.
    Xử lý tại chỗ res['long'], res['shorts'][i]['path'], ảnh bìa; trả (res, thumb, file_thêm[ảnh bìa dọc])."""
    cfg = load_cfg()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        msg = "thiếu ffmpeg/ffprobe, không kiểm tra được thông số nền tảng"
        if cfg.get("strict"):
            raise SpecError(msg)
        log("⚠️ " + msg)
        return res, thumb, []
    log("⑤b Chuẩn hoá thông số YouTube / TikTok / Reels")
    errs: list[str] = []
    extras: list[Path] = []
    jobs = [(Path(res["long"]), "long")] + [(Path(s["path"]), "short") for s in res.get("shorts", [])]
    for p, kind in jobs:
        try:
            process_video(p, kind, cfg)
        except SpecError as e:
            errs.append(str(e))
            continue
        errs += check_video(p, kind, cfg)
        if kind == "short" and cfg.get("vertical_cover"):
            c = vertical_cover(p, cfg)
            if c:
                extras.append(c)
    if thumb and Path(thumb).exists():
        try:
            thumb = process_thumb(Path(thumb), cfg)
            errs += check_thumb(thumb, cfg)
        except Exception as e:
            errs.append(f"ảnh bìa: {e}")
    if errs:
        msg = "Sai thông số xuất bản:\n- " + "\n- ".join(errs)
        if cfg.get("strict"):
            raise SpecError(msg)
        log("⚠️ " + msg)
    else:
        log("✅ Đạt chuẩn YouTube / Shorts / TikTok / Reels")
    return res, thumb, extras


def selftest() -> int:
    """Tạo video mẫu kiểu Remotion (1080p, BT.601 không nhãn, moov cuối file), chạy prepare, kiểm tra."""
    from PIL import Image
    d = Path(tempfile.mkdtemp(prefix="pe_selftest_"))
    try:
        def mk(name, w, h, sec):
            p = d / name
            r = _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"testsrc2=s={w}x{h}:r=30:d={sec}",
                      "-f", "lavfi", "-i", f"sine=f=440:r=44100:d={sec}", "-af", "volume=-6dB",
                      "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(p)])
            assert r.returncode == 0, r.stderr
            return p
        long_, short = mk("long.mp4", 1920, 1080, 4), mk("short.mp4", 1080, 1920, 3)
        th = d / "thumb.png"
        Image.new("RGB", (1920, 1080), (240, 240, 240)).save(th)
        res = {"long": long_, "shorts": [{"path": short}]}
        _, th2, extras = prepare(res, th)
        assert extras and extras[0].exists(), "không tạo được ảnh bìa dọc"
        _log("selftest OK:", long_.name, kind_of(long_), short.name, kind_of(short), th2.name, [e.name for e in extras])
        return 0
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, files = argv[0], [Path(x) for x in argv[1:]]
    if cmd == "selftest":
        return selftest()
    cfg = load_cfg()
    errs: list[str] = []
    for f in files:
        if f.suffix.lower() in (".png", ".jpg", ".jpeg"):
            if cmd == "fix":
                f = process_thumb(f, cfg)
            errs += check_thumb(f, cfg)
            continue
        k = kind_of(f)
        if cmd == "fix":
            process_video(f, k, cfg)
        errs += check_video(f, k, cfg)
    if errs:
        print("❌ Sai thông số:\n- " + "\n- ".join(errs))
        return 1
    print(f"✅ {len(files)} file đạt chuẩn")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
