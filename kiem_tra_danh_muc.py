# -*- coding: utf-8 -*-
"""
Kiểm tra hồ sơ chất lượng theo 3 vòng (không cần giao diện – dùng trong skill hoặc máy chủ):

  python kiem_tra_danh_muc.py <danh_muc.docx|pdf|xlsx> [<file 2> …]
         [--vong 1|2|3] [--loai GD|GT|HT|TT] [--vai-tro chinh|phu] [--quy-mo lon|hang_muc|nho]
         [--ngay dd/mm/yyyy] [--bc bao_cao_dang_tai.docx] [--vpdt danh_sach_vpdt.xlsx] [--sheets "Sheet1,CDC"]
         [--ocr] [--tiep-v3] [--bo-qua-vong1] [--nguoi "Họ tên"] [--out thu_muc]

Vòng 1 – kiểm tra đầu vào (định dạng, dung lượng, scan, file hỏng, ảnh dán vào Word) + nhận diện nhà thầu.
         TRẢ LẠI thì dừng, xuất phiếu vòng 1 và tin nhắn.
Vòng 2 – thành phần cốt lõi theo vai trò và quy mô nhà thầu. THIẾU HỒ SƠ CƠ BẢN thì dừng (trừ khi --tiep-v3).
Vòng 3 – đối chiếu chi tiết Phụ lục VII trong phạm vi quy mô nhà thầu.
Xuất: Phieu vong 1 ….docx, Phieu vong 2 ….docx, Phieu kiem tra ….docx + Doi chieu PL VII ….xlsx (vòng 3),
      Tin nhan ….txt (dán Zalo), ket_qua.json.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import kb  # noqa: E402
from core.checker import SEV_ICON, kiem_tra  # noqa: E402
from core.parser import doan_loai_nt, doc_danh_sach_vpdt, doc_file, doc_nhieu_file  # noqa: E402
from core.report_docx import xuat_docx  # noqa: E402
from core.report_vong import build_v1, build_v2  # noqa: E402
from core.report_xlsx import xuat_xlsx  # noqa: E402
from core.vong import KL_TRA_LAI, V2_THIEU, tin_nhan, vong1, vong1_noi_dung, vong2  # noqa: E402


def _chuyen_doi_cu(paths):
    """.doc/.xls → .docx/.xlsx bằng LibreOffice (nếu máy có); trả danh sách đường dẫn mới và ghi chú."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    out, notes = [], []
    tmp = None
    for p in paths:
        ext = p.lower().rsplit(".", 1)[-1]
        if ext in ("doc", "xls") and soffice:
            tmp = tmp or tempfile.mkdtemp(prefix="hscl_")
            target = "docx" if ext == "doc" else "xlsx"
            subprocess.run([soffice, "--headless", "--convert-to", target, "--outdir", tmp, p],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
            np_ = os.path.join(tmp, os.path.splitext(os.path.basename(p))[0] + "." + target)
            if os.path.exists(np_):
                out.append(np_)
                notes.append(f"Đã chuyển {os.path.basename(p)} → .{target} bằng LibreOffice.")
                continue
        out.append(p)
    return out, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="+", help="một quyển, hoặc nhiều danh mục rời (theo loại / theo đợt)")
    ap.add_argument("--vong", type=int, choices=[1, 2, 3], default=3, help="chạy đến vòng nào (mặc định 3)")
    ap.add_argument("--loai", choices=["HT", "GD", "GT", "TT"])
    ap.add_argument("--ngay")
    ap.add_argument("--vai-tro", dest="vai_tro", choices=["chinh", "phu"])
    ap.add_argument("--quy-mo", dest="quy_mo", choices=list(kb.QUY_MO))
    ap.add_argument("--bc")
    ap.add_argument("--vpdt")
    ap.add_argument("--sheets")
    ap.add_argument("--ocr", action="store_true", help="PDF scan: thử đọc bằng OCR (cần Tesseract tiếng Việt)")
    ap.add_argument("--tiep-v3", dest="tiep_v3", action="store_true", help="vẫn kiểm tra chi tiết khi vòng 2 thiếu hồ sơ cơ bản")
    ap.add_argument("--bo-qua-vong1", dest="bo_qua_v1", action="store_true")
    ap.add_argument("--nguoi", default="")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d")

    paths, notes = _chuyen_doi_cu(a.file)
    for n in notes:
        print("ℹ", n)
    files = [(os.path.basename(p), open(p, "rb").read()) for p in paths]
    base = os.path.splitext(files[0][0])[0][:60] if len(files) == 1 else f"Bo ho so {len(files)} danh muc"
    js = {"vong_da_chay": []}

    # ------------------------------------------------ vòng 1
    v1 = vong1(files, ocr=a.ocr)
    doc = None
    ok_files = [f for f, t in zip(files, v1.tep) if t["doc_duoc"] or a.bo_qua_v1]
    sh = a.sheets.split(",") if a.sheets else None
    bc_auto = None
    if ok_files:
        if len(ok_files) == 1 and not (sh and len(sh) > 1):
            doc = doc_file(ok_files[0][0], ok_files[0][1], sheets=sh, ocr=a.ocr)
        else:
            parts = []
            for fn, data in ok_files:
                if fn.lower().endswith(("xlsx", "xlsm")) and sh:
                    parts += [(f"{fn} › {x}", fn, data, x) for x in sh]
                else:
                    parts.append((fn, fn, data, None))
            doc, bc_auto, _ = doc_nhieu_file(parts, ocr=a.ocr)
    vong1_noi_dung(v1, doc, " ".join(f for f, _ in ok_files))
    nd = v1.nhan_dien or {}
    meta = (doc or {}).get("meta", {})
    info = dict(du_an=meta.get("du_an", ""), nha_thau=meta.get("nha_thau", "") or nd.get("nha_thau", ""),
                ho_so=files[0][0] if len(files) == 1 else f"{len(files)} file danh mục", nguoi=a.nguoi)
    p1 = os.path.join(a.out, f"Phieu vong 1 - kiem tra dau vao - {base} - {stamp}.docx")
    open(p1, "wb").write(build_v1(v1, info))
    js["vong1"] = v1.to_dict()
    js["vong_da_chay"].append(1)
    print(f"VÒNG 1 – KIỂM TRA ĐẦU VÀO: {v1.ket_luan} · {len(v1.tep_doc_duoc)}/{len(v1.tep)} file đọc được")
    for m in v1.muc:
        print(f"  [{m['muc']}] {(m['tep'] + ': ') if m.get('tep') else ''}{m['noi_dung']}")
    if nd:
        print(f"  Nhận diện: {'thầu phụ' if nd['vai_tro'] == 'phu' else 'thầu chính'} ({nd['ly_do_vai_tro']}) · "
              f"{kb.QUY_MO_NGAN[nd['quy_mo']]} ({nd['ly_do_quy_mo']}) · loại NT gợi ý {nd.get('loai_goi_y') or '?'}")
    print("→", p1)

    v2 = None
    if v1.tra_lai and not a.bo_qua_v1:
        msg = tin_nhan(v1, None, info)
    else:
        loai = a.loai or nd.get("loai_goi_y") or doan_loai_nt(meta, (doc or {}).get("text", "")) or "GD"
        vt = a.vai_tro or nd.get("vai_tro", "chinh")
        qm = a.quy_mo or nd.get("quy_mo", "lon")
        msg = tin_nhan(v1, None, info)
        if a.vong >= 2:
            # ------------------------------------------------ vòng 2
            v2 = vong2(doc, loai, vt, qm)
            p2 = os.path.join(a.out, f"Phieu vong 2 - ra soat so bo - {base} - {stamp}.docx")
            open(p2, "wb").write(build_v2(v2, v1, info))
            js["vong2"] = v2.to_dict()
            js["vong_da_chay"].append(2)
            msg = tin_nhan(v1, v2, info)
            print(f"VÒNG 2 – RÀ SOÁT SƠ BỘ ({kb.LOAI_NT[loai]} · {'thầu phụ' if vt == 'phu' else 'thầu chính'} · "
                  f"{kb.QUY_MO_NGAN[qm]}): {v2.ket_luan}")
            for c in v2.thanh_phan:
                ic = {"co": "🟢", "thieu_dm": "🟠"}.get(c["trang_thai"], "🔴" if c["chan"] else "🟠")
                print(f"  {ic} {c['ten']} – {c['trang_thai']} ({c['so_dong']} dòng)")
            print("→", p2)
            if a.vong >= 3 and (v2.ket_luan != V2_THIEU or a.tiep_v3):
                # ------------------------------------------------ vòng 3
                ngay = datetime.strptime(a.ngay, "%d/%m/%Y").date() if a.ngay else None
                bc = doc_file(os.path.basename(a.bc), open(a.bc, "rb").read()) if a.bc else bc_auto
                vp = doc_danh_sach_vpdt(os.path.basename(a.vpdt), open(a.vpdt, "rb").read()) if a.vpdt else None
                R = kiem_tra(doc, loai, ngay_nt=ngay, bc_dang_tai=bc, ds_vpdt=vp, vai_tro=vt, quy_mo=qm)
                R["vong"] = {"v1": v1.ket_luan, "v2": v2.ket_luan}
                ten = files[0][0] if len(files) == 1 else f"Bộ hồ sơ {len(files)} danh mục"
                p_docx = os.path.join(a.out, f"Phieu kiem tra HS chat luong - {base} - {stamp}.docx")
                p_xlsx = os.path.join(a.out, f"Doi chieu PL VII - {base} - {stamp}.xlsx")
                open(p_docx, "wb").write(xuat_docx(R, a.nguoi, ten))
                open(p_xlsx, "wb").write(xuat_xlsx(R, ten))
                js["vong_da_chay"].append(3)
                for kk in ("meta", "loai_nt", "vai_tro", "quy_mo", "nghi_dinh", "kpi", "ket_luan", "findings", "cau_hoi",
                           "cau_hoi_muc", "warnings"):
                    js[kk] = R[kk]
                js["items"] = [{x: it[x] for x in ("code", "ten", "yeu_cau", "trang_thai", "ket_luan", "so_dong", "ma", "dong")}
                               for it in R["items"]]
                js["ma_map"] = {m: {"dong": e["dong"], "dong_ke_thua": e["dong_ke_thua"],
                                    "muc": sorted(c for c in e["muc"] if c), "gom": e.get("gom", False)}
                                for m, e in R["ma_map"].items()}
                js["rows"] = [{x: r.get(x) for x in ("id", "cap", "cha", "stt", "noi_dung", "so_vb", "ngay_raw", "don_vi", "ma",
                                                     "ma_ke_thua", "muc", "muc_nguon", "tinh_trang")} for r in R["rows"]]
                k = R["kpi"]
                print(f"VÒNG 3 – KIỂM TRA CHI TIẾT ({R['nghi_dinh']}): {R['ket_luan']}")
                print(f"  Mục B có {k['muc_B_co']}/{k['muc_B']} · dòng chi tiết {k['dong_chi_tiet']} · có mã {k['ty_le_co_ma']}% · "
                      f"mã HS {k['so_ma']} (gom {k['so_ma_gom']}) · 🔴{k['high']} 🟠{k['mid']} 🔵{k['info']}")
                for f in R["findings"]:
                    print(f"  {SEV_ICON[f['muc_do']]} [{f['ma_loi']}] {f['tieu_de']}")
                print("→", p_docx)
                print("→", p_xlsx)
            elif a.vong >= 3:
                print("  Dừng sau vòng 2: thiếu hồ sơ cơ bản (thêm --tiep-v3 nếu vẫn muốn kiểm tra chi tiết).")
    p_msg = os.path.join(a.out, f"Tin nhan gui doan - {base} - {stamp}.txt")
    open(p_msg, "w", encoding="utf-8").write(msg)
    js["tin_nhan"] = msg
    with open(os.path.join(a.out, "ket_qua.json"), "w", encoding="utf-8") as f:
        json.dump(js, f, ensure_ascii=False, indent=1, default=str)
    print("→", p_msg)
    print("----- TIN NHẮN (dán Zalo) -----")
    print(msg)


if __name__ == "__main__":
    main()
