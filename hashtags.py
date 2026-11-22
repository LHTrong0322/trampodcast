"""Ghép caption + hashtag không trùng, tối đa 5 (Trọng 22/11: caption bị spam hashtag)."""
import re


def with_tags(caption: str, tags, limit: int = 5) -> str:
    """Trọng 22/11: caption bị spam hashtag (máy viết sẵn hashtag trong caption rồi lại nối thêm danh sách → trùng).
    Gom hashtag trong caption + danh sách, bỏ trùng (không phân biệt hoa thường), tối đa `limit` cái, đặt cuối caption."""
    caption = caption or ""
    found = re.findall(r"#[\wÀ-ỹ]+", caption)
    body = re.sub(r"\s*#[\wÀ-ỹ]+", "", caption).strip()
    out, seen = [], set()
    for t in found + [x if str(x).startswith("#") else "#" + str(x) for x in (tags or [])]:
        k = t.lower()
        if k not in seen and len(t) > 1:
            seen.add(k)
            out.append(t)
    return (body + " " + " ".join(out[:limit])).strip()
