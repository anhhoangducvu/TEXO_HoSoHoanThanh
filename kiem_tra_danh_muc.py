# -*- coding: utf-8 -*-
"""
Chạy bộ lọc không cần giao diện (dùng trong skill hoặc máy chủ):

  python kiem_tra_danh_muc.py <danh_muc.docx|pdf|xlsx> [--loai HT|GD|GT] [--ngay dd/mm/yyyy]
         [--bc bao_cao_dang_tai.docx] [--vpdt danh_sach_vpdt.xlsx] [--sheets "Sheet1,CDC"]
         [--nguoi "Họ tên"] [--out thu_muc]

Xuất: Phieu kiem tra ....docx, Doi chieu PL VII ....xlsx, ket_qua.json; in tóm tắt ra màn hình.
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.checker import SEV_ICON, kiem_tra  # noqa: E402
from core.parser import doan_loai_nt, doc_danh_sach_vpdt, doc_file  # noqa: E402
from core.report_docx import xuat_docx  # noqa: E402
from core.report_xlsx import xuat_xlsx  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--loai", choices=["HT", "GD", "GT"])
    ap.add_argument("--ngay")
    ap.add_argument("--vai-tro", dest="vai_tro", choices=["chinh", "phu"])
    ap.add_argument("--bc")
    ap.add_argument("--vpdt")
    ap.add_argument("--sheets")
    ap.add_argument("--nguoi", default="")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()

    name = os.path.basename(a.file)
    doc = doc_file(name, open(a.file, "rb").read(), sheets=a.sheets.split(",") if a.sheets else None)
    loai = a.loai or doan_loai_nt(doc["meta"], doc["text"]) or "HT"
    ngay = datetime.strptime(a.ngay, "%d/%m/%Y").date() if a.ngay else None
    bc = doc_file(os.path.basename(a.bc), open(a.bc, "rb").read()) if a.bc else None
    vp = doc_danh_sach_vpdt(os.path.basename(a.vpdt), open(a.vpdt, "rb").read()) if a.vpdt else None
    vt = a.vai_tro or ("phu" if doc["meta"].get("tong_thau") else "chinh")
    R = kiem_tra(doc, loai, ngay_nt=ngay, bc_dang_tai=bc, ds_vpdt=vp, vai_tro=vt)

    os.makedirs(a.out, exist_ok=True)
    base = os.path.splitext(name)[0][:60]
    stamp = datetime.now().strftime("%Y%m%d")
    p_docx = os.path.join(a.out, f"Phieu kiem tra HS chat luong - {base} - {stamp}.docx")
    p_xlsx = os.path.join(a.out, f"Doi chieu PL VII - {base} - {stamp}.xlsx")
    open(p_docx, "wb").write(xuat_docx(R, a.nguoi, name))
    open(p_xlsx, "wb").write(xuat_xlsx(R, name))
    js = {k: R[k] for k in ("meta", "loai_nt", "vai_tro", "nghi_dinh", "kpi", "ket_luan", "findings", "cau_hoi", "cau_hoi_muc", "warnings")}
    js["items"] = [{k: it[k] for k in ("code", "ten", "yeu_cau", "trang_thai", "ket_luan", "so_dong", "ma", "dong")} for it in R["items"]]
    js["ma_map"] = {m: {"dong": e["dong"], "dong_ke_thua": e["dong_ke_thua"], "muc": sorted(c for c in e["muc"] if c),
                        "gom": e.get("gom", False)} for m, e in R["ma_map"].items()}
    js["rows"] = [{k: r.get(k) for k in ("id", "cap", "cha", "stt", "noi_dung", "so_vb", "ngay_raw", "don_vi", "ma",
                                          "ma_ke_thua", "muc", "muc_nguon", "tinh_trang")} for r in R["rows"]]
    with open(os.path.join(a.out, "ket_qua.json"), "w", encoding="utf-8") as f:
        json.dump(js, f, ensure_ascii=False, indent=1, default=str)

    k = R["kpi"]
    print(f"Tài liệu: {R['meta'].get('tieu_de', name)} · kiểu {R['info'].get('kieu')} · {R['loai_nt_label']} · {R['nghi_dinh']}")
    for w in R["warnings"]:
        print("⚠", w)
    print(f"KẾT LUẬN: {R['ket_luan']}")
    print(f"Mục B có {k['muc_B_co']}/{k['muc_B']} · dòng chi tiết {k['dong_chi_tiet']} · có mã {k['ty_le_co_ma']}% · "
          f"mã HS {k['so_ma']} (gom {k['so_ma_gom']}) · 🔴{k['high']} 🟠{k['mid']} 🔵{k['info']}")
    for f in R["findings"]:
        print(f"{SEV_ICON[f['muc_do']]} [{f['ma_loi']}] {f['tieu_de']}")
    print("→", p_docx)
    print("→", p_xlsx)


if __name__ == "__main__":
    main()
