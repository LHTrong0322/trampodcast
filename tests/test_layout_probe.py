"""Trọng 28/11: máy đo bố cục chỉ báo lỗi kéo dài (không báo khung đang chuyển cảnh)."""
import layout_lint as LL


def _raw(issue_ts, step=0.5, n=20, kind="bi_che"):
    return {"frames": [{"t": i * step, "texts": ["Lý thuyết Dow"], "issues":
                        ([{"kind": kind, "text": "thật", "other": "381 vs 41"}] if i * step in issue_ts else [])} for i in range(n)]}


def test_loi_keo_dai_thi_bao():
    iss = LL.persistent(_raw({2.0, 2.5, 3.0, 3.5}))
    assert len(iss) == 1 and iss[0]["start"] == 2.0 and iss[0]["end"] == 3.5
    assert "che một phần" in LL.report(iss)[0]


def test_loi_thoang_qua_khi_chuyen_canh_thi_bo_qua():
    assert LL.persistent(_raw({4.0})) == []


def test_gom_chu_de_soat_chinh_ta():
    assert LL.texts(_raw(set())) == ["Lý thuyết Dow"]


def test_may_do_loi_khong_lam_hong_luot_dung(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("chrome chết")
    monkeypatch.setattr(LL, "run", boom)
    r = LL.check({}, tmp_path)
    assert r["ok"] is None and r["issues"] == []
