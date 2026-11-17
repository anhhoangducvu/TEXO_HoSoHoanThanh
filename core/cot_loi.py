# -*- coding: utf-8 -*-
"""
Nhận diện nhà thầu và tìm THÀNH PHẦN CỐT LÕI trong bộ danh mục – dùng chung cho vòng 1, vòng 2 (vong.py)
và vòng 3 (checker.py). Quy tắc nằm ở core/kb.py (NT_*, THANH_PHAN_COT_LOI, BBNT_THEO_LOAI).
"""
import re

from . import kb
from .parser import norm

_RE = {}


def _re(p):
    if p not in _RE:
        _RE[p] = re.compile(p)
    return _RE[p]


def _tim(pats, text):
    for p in pats:
        m = _re(p).search(text)
        if m:
            return m.group(0)
    return None


# ----------------------------------------------------------------------------- nhận diện nhà thầu
def nhan_dien_nha_thau(doc, ten_file=""):
    """Gợi ý vai trò (chinh/phu) và quy mô (lon/hang_muc/nho) từ tiêu đề, gói thầu, hạng mục, tên file, phần đầu văn bản.
    Trả dict(vai_tro, quy_mo, nha_thau, pham_vi, ly_do_vai_tro, ly_do_quy_mo, chac_chan)."""
    meta = doc.get("meta", {}) if doc else {}
    tep = " ".join(t.get("ten", "") + " " + t.get("tieu_de", "") for t in (doc or {}).get("tep") or [])
    pham_vi_raw = " · ".join(x for x in (meta.get("goi_thau"), meta.get("hang_muc")) if x)
    dau = norm(" ".join([meta.get("tieu_de", ""), meta.get("goi_thau", ""), meta.get("hang_muc", ""),
                         meta.get("nha_thau", ""), ten_file or "", tep]).replace("_", " ").replace("-", " "))
    than = norm(str((doc or {}).get("text", ""))[:2500])
    toan_bo = norm(" ".join(str(r.get("noi_dung", "")) for r in (doc or {}).get("rows") or [])[:200000])
    # vai trò
    vt, ly_vt = "chinh", ""
    if meta.get("tong_thau"):
        vt, ly_vt = "phu", f"danh mục có dòng Tổng thầu: {meta['tong_thau'][:60]}"
    else:
        hit = _tim(kb.NT_PHU, dau) or _tim(kb.NT_PHU, than)
        if hit:
            vt, ly_vt = "phu", f"có cụm “{hit}”"
    # quy mô: ưu tiên phần tiêu đề / phạm vi
    qm, ly_qm, chac = None, "", True
    for src, nguon in ((dau, "tiêu đề / gói thầu / tên file"), (than, "nội dung danh mục")):
        h_lon = _tim(kb.NT_LON, src)
        h_hm = _tim(kb.NT_HANG_MUC, src)
        h_nho = _tim(kb.NT_NHO, src)
        if h_lon and not (vt == "phu" and h_lon in ("tong thau", "thau chinh")):
            qm, ly_qm = "lon", f"{nguon} có “{h_lon}”"
        elif h_hm:
            qm, ly_qm = "hang_muc", f"{nguon} có “{h_hm}”"
        elif h_nho:
            qm, ly_qm = "nho", f"{nguon} có “{h_nho}”"
        if qm:
            chac = nguon != "nội dung danh mục"
            break
    # danh mục trải nhiều phần việc (cọc + móng + kết cấu + hoàn thiện…) → nhiều khả năng thầu chính / tổng thầu
    nhom = [g for g, p in kb.NT_NHOM_VIEC.items() if _re(p).search(toan_bo)]
    if len(nhom) >= 3 and qm != "lon" and not (chac and qm):
        qm, ly_qm, chac = "lon", "danh mục gồm nhiều phần việc: " + ", ".join(nhom[:5]), False
    if not qm:
        qm, ly_qm, chac = ("hang_muc" if vt == "phu" else "lon"), "chưa thấy phạm vi công việc – cần người kiểm tra chọn", False
    return dict(vai_tro=vt, quy_mo=qm, nha_thau=meta.get("nha_thau", ""), pham_vi=pham_vi_raw,
                ly_do_vai_tro=ly_vt or "không thấy dấu hiệu thầu phụ", ly_do_quy_mo=ly_qm, chac_chan=chac)


# ----------------------------------------------------------------------------- thành phần cốt lõi
def thanh_phan_ap_dung(loai, vai_tro, quy_mo):
    out = []
    for c in kb.THANH_PHAN_COT_LOI:
        if c["ap"] != "all" and quy_mo not in c["ap"]:
            continue
        if c.get("thau_phu") and vai_tro != "phu":
            continue
        c = dict(c)
        if c["key"] == "BBNT":
            c["ten"], c["pat"] = kb.BBNT_THEO_LOAI.get(loai, kb.BBNT_THEO_LOAI["GD"])
            if loai == "HT":
                c["muc"] = {"III.13"}
        c["chan_that"] = bool(c.get("chan")) and loai not in c.get("khong_chan", set())
        out.append(c)
    return out


def _con_chau(rows_by_parent, rid, seen=None):
    seen = seen if seen is not None else set()
    for r in rows_by_parent.get(rid, []):
        if r["id"] not in seen:
            seen.add(r["id"])
            _con_chau(rows_by_parent, r["id"], seen)
    return seen


def tim_thanh_phan(rows, tep, loai, vai_tro, quy_mo):
    """rows đã gán mục (checker.gan_muc). Trả danh sách dict(key, ten, chan, trang_thai, dong, so_chi_tiet, cau_hoi).
    trang_thai: co | thieu_dm (có tên quyển, chưa có danh mục chi tiết) | thieu."""
    by_parent = {}
    for r in rows:
        by_parent.setdefault(r.get("cha"), []).append(r)
    by_id = {r["id"]: r for r in rows}
    txt = {r["id"]: norm(f'{r.get("noi_dung", "")} {r.get("so_vb", "")}') for r in rows}
    out = []
    for c in thanh_phan_ap_dung(loai, vai_tro, quy_mo):
        hit = []
        for r in rows:
            if r.get("la_tep"):
                continue
            t = txt[r["id"]]
            if c.get("loai_tru") and _re(c["loai_tru"]).search(t):
                continue
            ok = False
            if r.get("muc") in c.get("muc", set()) and (not c.get("loc") or _re(c["loc"]).search(t)):
                ok = True
            elif c.get("pat") and _re(c["pat"]).search(t):
                ok = True
            if ok:
                hit.append(r)
        tep_hit = [t for t in (tep or []) if t.get("loai") in c.get("tep", set()) and t.get("so_dong")]
        ids = {r["id"] for r in hit}
        for r in list(hit):
            ids |= _con_chau(by_parent, r["id"])
        for t in tep_hit:
            if t.get("id_nhom"):
                ids |= _con_chau(by_parent, t["id_nhom"])
        dong = sorted(ids)
        chi_tiet = [by_id[i] for i in dong if i in by_id and (by_id[i].get("so_vb") or by_id[i].get("ngay_raw")
                                                               or not by_parent.get(i))]
        if not dong:
            tt = "thieu"
        elif c.get("danh_muc") and len(chi_tiet) <= 1 and not any(by_id[i].get("so_vb") for i in dong if i in by_id):
            tt = "thieu_dm"
        else:
            tt = "co"
        out.append(dict(key=c["key"], ten=c["ten"], chan=c["chan_that"], danh_muc=bool(c.get("danh_muc")),
                        trang_thai=tt, dong=dong[:60], so_dong=len(dong), so_chi_tiet=len(chi_tiet),
                        mau=[by_id[i]["noi_dung"][:90] for i in dong[:3] if i in by_id],
                        tep=[t["ten"] for t in tep_hit], cau_hoi=c["cau_hoi"]))
    return out
