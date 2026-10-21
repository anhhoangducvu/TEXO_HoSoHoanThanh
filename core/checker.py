# -*- coding: utf-8 -*-
"""
BỘ LỌC ĐỐI CHIẾU danh mục hồ sơ hoàn thành với Phụ lục VII NĐ 207/2026 (rule-based, chạy cục bộ).

kiem_tra(doc, loai_nt, ngay_nt=None, bc_dang_tai=None, ds_vpdt=None) → dict kết quả:
  rows      : dòng đã phân loại (mục PL VII, mã hiệu lực, cờ)
  items     : trạng thái từng mục PL VII theo loại nghiệm thu
  ma_map    : bản đồ mã VPĐT → các dòng, các mục
  findings  : phát hiện có mức độ (high = Phải xử lý, mid = Nên xử lý, info = Lưu ý)
  kpi       : số liệu tổng quan
  cau_hoi   : câu hỏi gợi ý cho đoàn tư vấn
"""
import re
from collections import defaultdict, OrderedDict
from datetime import date

from . import kb
from .parser import norm, doc_ngay

SEV_ORDER = {"high": 0, "mid": 1, "info": 2}
SEV_ICON = {"high": "🔴", "mid": "🟠", "info": "🔵", "ok": "🟢", "na": "⚪"}
SEV_LABEL = {"high": "Phải xử lý", "mid": "Nên xử lý", "info": "Lưu ý", "ok": "Đạt", "na": "Không xét"}


# ----------------------------------------------------------------------------- phân loại
_COMPILED = {m["code"]: ([re.compile(p) for p in m["tu_khoa"]], [re.compile(p) for p in m.get("loai_tru", [])])
             for m in kb.MUC}


def phan_loai(text):
    t = norm(text)
    if not t:
        return None
    for code in kb.UU_TIEN:
        inc, exc = _COMPILED[code]
        if any(p.search(t) for p in inc) and not any(p.search(t) for p in exc):
            return code
    return None


def _la_tieu_de_nhom_chung(t):
    t = norm(t)
    return bool(re.fullmatch(r"(ho so )?(phap ly|chat luong|an toan.*|ban ve.*|khac|chung)( cong trinh| nha thau| chung)?", t)) \
        or t in ("ho so phap ly", "cac quyet dinh phe duyet", "ho so phap ly nha thau")


def gan_muc(rows):
    by_id = {r["id"]: r for r in rows}
    for r in rows:
        if r.get("muc_nguon") == "ai" and r.get("muc"):
            r["ma_hl"] = r["ma"] or r["ma_ke_thua"]
            continue  # giữ phân loại AI đã được áp dụng
        txt = f'{r["noi_dung"]} {r["so_vb"]}'
        own = phan_loai(txt)
        # tiêu đề nhóm lớn kiểu "HỒ SƠ PHÁP LÝ" không gán; "HỒ SƠ CHẤT LƯỢNG" để con tự phân loại
        if r["cap"] == 0 and own in ("III.6", "I.9", None) and _la_tieu_de_nhom_chung(r["noi_dung"]):
            own = None
        par0 = by_id.get(r["cha"])
        if own in ("I.8", "III.16", "I.9") and par0 and par0.get("muc") and par0["muc"] != own and par0["cap"] > 0 \
                and par0["muc"] not in ("T.9",):
            # dòng chung chung (hợp đồng, phụ lục…) nằm trong nhóm đã rõ mục → theo nhóm
            r["muc"], r["muc_nguon"] = par0["muc"], "ke_thua"
        elif own:
            r["muc"], r["muc_nguon"] = own, "tu_khoa"
        else:
            par = by_id.get(r["cha"])
            if par and par.get("muc") and par["cap"] > 0:
                r["muc"], r["muc_nguon"] = par["muc"], "ke_thua"
            elif par and par.get("muc") and par["cap"] == 0 and kb.MUC_BY_CODE[par["muc"]]["hinh_thuc"] == "QUYEN":
                r["muc"], r["muc_nguon"] = par["muc"], "ke_thua"
            else:
                r["muc"], r["muc_nguon"] = None, None
        r["ma_hl"] = r["ma"] or r["ma_ke_thua"]
    return rows


def ap_dung_ai(rows, bo_sung):
    """bo_sung = [{dong: id, muc: code}] từ AI → ghi đè dòng chưa phân loại hoặc phân loại kế thừa."""
    by_id = {r["id"]: r for r in rows}
    n = 0
    for b in bo_sung or []:
        try:
            rid = int(b.get("dong"))
        except Exception:
            continue
        code = str(b.get("muc", "")).strip()
        if rid in by_id and code in kb.MUC_BY_CODE:
            by_id[rid]["muc"], by_id[rid]["muc_nguon"] = code, "ai"
            n += 1
    return n


# ----------------------------------------------------------------------------- tiện ích
def _la_dong_chi_tiet(r):
    """Dòng thể hiện một tài liệu cụ thể (không phải tiêu đề nhóm)."""
    return bool(r["so_vb"] or r["ngay_raw"]) or (r["so_con"] == 0 and r["cap"] > 0)


def _nhom_pl(code):
    return code.split(".")[0] if code else None


def _fmt_ids(ids, n=12):
    ids = list(ids)
    s = ", ".join(str(i) for i in ids[:n])
    return s + (f" … (+{len(ids) - n})" if len(ids) > n else "")


def _f(findings, sev, ma_loi, tieu_de, chi_tiet="", dong=None, muc=None, de_xuat=""):
    findings.append(dict(muc_do=sev, ma_loi=ma_loi, tieu_de=tieu_de, chi_tiet=chi_tiet,
                         dong=list(dong or []), muc_pl=muc, de_xuat=de_xuat))


# ----------------------------------------------------------------------------- kiểm tra chính
def kiem_tra(doc, loai_nt="HT", ngay_nt=None, bc_dang_tai=None, ds_vpdt=None, hom_nay=None, vai_tro="chinh"):
    """vai_tro: "chinh" – tổng thầu / thầu chính (kiểm tra kỹ pháp lý dự án); "phu" – thầu phụ / nhà thầu nhỏ."""
    hom_nay = hom_nay or date.today()
    rows = gan_muc(doc["rows"])
    meta = doc.get("meta", {})
    info = doc.get("info", {})
    cot = set(info.get("co_cot", []))
    cot_ma = "ma" in cot or any(r["ma"] for r in rows)
    cot_tt = "tinh_trang" in cot
    col = kb.COT_MA_TRAN.get(loai_nt, "HT")
    findings = []

    # ---------------- 0. loại tài liệu, nghị định
    if info.get("kieu") == "BAO_CAO_DANG_TAI":
        _f(findings, "mid", "F17", "Tài liệu là BÁO CÁO ĐĂNG TẢI nội bộ, chưa phải quyển danh mục hồ sơ hoàn thành",
           "Báo cáo đăng tải chỉ liệt kê mã hồ sơ đã đưa lên VPĐT; nhiều nhóm hồ sơ có thể bị gom vào một mã. "
           "Danh mục hồ sơ hoàn thành theo Điều 28 và Phụ lục VII phải liệt kê từng thành phần hồ sơ theo thứ tự, kèm số/ngày văn bản.",
           de_xuat="Lập quyển Danh mục hồ sơ hoàn thành theo 3 phần của Phụ lục VII; dùng báo cáo đăng tải làm cột 'Mã TEXO-E'.")
    nghi_dinh = "NĐ 207/2026"
    if ngay_nt:
        if ngay_nt < date(*kb.NGAY_HIEU_LUC_207):
            nghi_dinh = "NĐ 06/2021"
            _f(findings, "info", "F13", "Ngày nghiệm thu trước 01/7/2026 → căn cứ NĐ 06/2021 (Phụ lục VIb)",
               "Danh mục đối chiếu dùng Phụ lục VII NĐ 207 (nội dung tương đương phần lớn Phụ lục VIb NĐ 06). "
               "Văn bản dẫn NĐ 06/2021 trong trường hợp này không phải lỗi; kiểm tra ngày các tài liệu không muộn hơn ngày nghiệm thu.")
    txt_all = norm(doc.get("text", ""))
    if nghi_dinh == "NĐ 207/2026" and re.search(r"06/2021/nd-cp|nghi dinh (so )?06/2021", txt_all):
        _f(findings, "mid", "F13", "Tài liệu còn dẫn NĐ 06/2021 trong khi nghiệm thu áp dụng NĐ 207/2026",
           "NĐ 06/2021 hết hiệu lực từ 01/7/2026 (Điều 52 NĐ 207). Nếu ngày nghiệm thu thực tế trước 01/7/2026 thì nhập lại ngày nghiệm thu để công cụ chấm theo NĐ 06.",
           de_xuat="Cập nhật căn cứ pháp lý hoặc xác nhận lại ngày nghiệm thu.")

    # ---------------- 1. thông tin chung
    thieu = [lab for k, lab in (("du_an", "Dự án"), ("chu_dau_tu", "Chủ đầu tư"), ("nha_thau", "Nhà thầu thi công"),
                                ("dia_diem", "Địa điểm")) if not meta.get(k)]
    if not (meta.get("hang_muc") or meta.get("goi_thau")):
        thieu.append("Hạng mục / gói thầu")
    if not meta.get("hop_dong") and not any(r["muc"] == "I.8" and r["so_vb"] for r in rows):
        thieu.append("Số hợp đồng")
    if thieu:
        _f(findings, "info", "F12", "Phần thông tin chung của danh mục còn thiếu: " + ", ".join(thieu),
           "Quyển danh mục cần thể hiện rõ dự án, hạng mục/gói thầu, địa điểm, chủ đầu tư, các nhà thầu và số hợp đồng để xác định phạm vi hồ sơ.",
           de_xuat="Bổ sung khối thông tin chung ở đầu danh mục.")
    if not any(r["cap"] == 0 for r in rows) and info.get("kieu") != "BAO_CAO_DANG_TAI":
        _f(findings, "info", "F18", "Danh mục chưa chia nhóm theo 3 phần của Phụ lục VII",
           "Nên sắp theo: I. Chuẩn bị đầu tư và hợp đồng · II. Khảo sát, thiết kế · III. Quản lý thi công – để người đọc nắm trình tự hồ sơ.")

    # ---------------- 2. trạng thái từng mục PL VII
    by_muc = defaultdict(list)
    for r in rows:
        if r.get("muc"):
            by_muc[r["muc"]].append(r)
    items = []
    thieu_cdt, thieu_neu_co = [], []
    co_hs_chat_luong = any(re.search(r"ho so (chat luong|nghiem thu)|hoan thanh goi thau", norm(r["noi_dung"])) for r in rows)
    for m in kb.MUC:
        code = m["code"]
        yc = m["ap_dung"][col]
        if vai_tro == "phu" and yc == "B" and code in kb.CDT_LUU and code not in ("I.2", "I.7"):
            yc = "Đ"  # thầu phụ / nhà thầu nhỏ: pháp lý dự án chỉ đối chiếu nếu có
        rs = by_muc.get(code, [])
        ct = [r for r in rs if _la_dong_chi_tiet(r)]
        co_sh = [r for r in rs if r["so_vb"] or r["ngay_raw"]]
        co_ma = [r for r in rs if r["ma_hl"]]
        mas = sorted({x for r in rs for x in r["ma_hl"]})
        van_de = []
        if rs:
            if m["hinh_thuc"] in ("VB", "PD") and not co_sh and code not in ("T.1", "T.2", "T.9"):
                van_de.append("chưa ghi số/ngày văn bản" + (" phê duyệt/chấp thuận" if m["hinh_thuc"] == "PD" else ""))
            if m["hinh_thuc"] == "QUYEN" and m["can_dm_kem"] and len(ct) <= 1 and not co_sh:
                van_de.append("mới có tên quyển, chưa có danh mục chi tiết kèm theo")
        ghi_ma = bool(rs and cot_ma and not co_ma and yc != "-")
        if yc == "-":
            tt = "na" if not rs else "info"
            kl = "Không xét" if not rs else "Có trong danh mục (ngoài phạm vi loại nghiệm thu này)"
        elif not rs:
            if yc == "B":
                if m["neu_co"]:
                    tt, kl = "mid", "Chưa thấy – nếu không có phải ghi rõ “Không có”"
                else:
                    tt = "high" if code in kb.MUC_COT_LOI.get(col, set()) else "mid"
                    kl = "Chưa thấy trong danh mục"
            else:
                tt, kl = "info", "Không thấy (đối chiếu nếu có)"
        else:
            if van_de:
                tt, kl = "mid", "Có – " + "; ".join(van_de)
            else:
                tt, kl = "ok", "Có"
            if ghi_ma:
                kl += " · chưa đăng tải / chưa thể hiện mã VPĐT"
        items.append(dict(code=code, nhom=_nhom_pl(code), ten=m["ten"], nguyen_van=m["nguyen_van"],
                          hinh_thuc=m["hinh_thuc"], hinh_thuc_label=kb.HINH_THUC_LABEL[m["hinh_thuc"]],
                          can_dm_kem=m["can_dm_kem"], yeu_cau=yc, trang_thai=tt, ket_luan=kl,
                          so_dong=len(rs), so_chi_tiet=len(ct), so_co_so_hieu=len(co_sh), ma=mas,
                          dong=[r["id"] for r in rs], van_de=van_de))
        items[-1]["chu_the"] = m.get("chu_the", "")
        if yc != "-" and tt in ("high", "mid"):
            if not rs:
                if tt == "mid" and m["neu_co"] and code != "III.10b":
                    thieu_neu_co.append(items[-1])
                elif tt == "mid" and m.get("chu_the") == "CĐT" and code != "I.7":
                    thieu_cdt.append(items[-1])
                else:
                    ghi = m["nguyen_van"]
                    if code in ("III.4", "III.5", "III.6") and co_hs_chat_luong:
                        ghi += (" Danh mục có các dòng 'Hồ sơ chất lượng …' – thành phần này có thể nằm bên trong "
                                "nhưng danh mục không thể hiện được; cần danh mục con của từng quyển.")
                    _f(findings, tt, "F01", f"Mục {code} – {m['ten']}: {kl.lower()}", ghi,
                       muc=code, de_xuat=kb.CAU_HOI.get(code, "Bổ sung hoặc ghi rõ lý do không có."))
            else:
                _f(findings, "mid", "F02", f"Mục {code} – {m['ten']}: " + "; ".join(van_de),
                   f"{len(rs)} dòng thuộc mục này (dòng {_fmt_ids(r['id'] for r in rs)}). Yêu cầu hình thức: {kb.HINH_THUC_LABEL[m['hinh_thuc']]}.",
                   dong=[r["id"] for r in rs], muc=code, de_xuat=kb.CAU_HOI.get(code, "Bổ sung thông tin còn thiếu."))

    if thieu_cdt:
        _f(findings, "mid", "F01", f"{len(thieu_cdt)} mục hồ sơ pháp lý dự án (do Chủ đầu tư lập, lưu) chưa được dẫn trong danh mục",
           " · ".join(f"{it['code']} {it['ten']}" for it in thieu_cdt) +
           ". Danh mục hoàn thành hạng mục/gói thầu không cần kèm bản gốc nhưng nên dẫn số hiệu văn bản để người đọc biết căn cứ.",
           muc=",".join(it["code"] for it in thieu_cdt),
           de_xuat="Dẫn số, ngày các văn bản pháp lý dự án (hoặc ghi 'CĐT lưu tại …'); mục không phát sinh ghi 'Không có'.")
    if thieu_neu_co:
        _f(findings, "mid", "F01", f"{len(thieu_neu_co)} mục ghi “(nếu có)” trong PL VII chưa thấy và chưa ghi rõ “Không có”",
           " · ".join(f"{it['code']} {it['ten']}" for it in thieu_neu_co),
           muc=",".join(it["code"] for it in thieu_neu_co),
           de_xuat="Với mục không phát sinh, ghi dòng 'Không có' để chứng minh đã xem xét đủ danh mục.")

    # ---------------- 2b. kiểm tra sâu một số mục
    txt_rows = {r["id"]: norm(r["noi_dung"] + " " + r["so_vb"]) for r in rows}
    t_i9 = " ".join(txt_rows[r["id"]] for r in rows if r.get("muc") in ("I.9", "III.16"))
    if by_muc.get("I.9"):
        thieu9 = [k for k, p in kb.I9_THANH_PHAN.items() if not re.search(p, t_i9)]
        if thieu9:
            _f(findings, "mid", "F20", "Hồ sơ năng lực nhà thầu (I.9) chưa thể hiện đủ thành phần tối thiểu: " + ", ".join(thieu9),
               "Tối thiểu cần: hồ sơ năng lực/kinh nghiệm, sơ đồ tổ chức, nhân sự, máy móc thiết bị thi công.", muc="I.9",
               de_xuat="Bổ sung các thành phần còn thiếu; đề nghị nhà thầu làm rõ năng lực tài chính.")
    t_all = " ".join(txt_rows.values())
    co_tb = bool(by_muc.get("III.8")) or bool(re.search(r"thiet bi (lap dat|cong nghe)|may bom|tram bom|thang may|dieu hoa|may phat|tu dien", t_all))
    if co_tb and col == "HT":
        t8 = " ".join(txt_rows[r["id"]] for r in rows if r.get("muc") in ("III.8", "III.6", "III.16")) + " " + t_all
        thieu8 = [k for k, p in kb.III8_THANH_PHAN.items() if not re.search(p, t8)]
        if thieu8:
            _f(findings, "mid", "F21", "Hạng mục có thiết bị nhưng danh mục chưa thể hiện: " + ", ".join(thieu8),
               "Hồ sơ QLCL thiết bị lắp đặt (III.8) cần có hồ sơ lắp đặt, biên bản chạy thử đơn động và chạy thử liên động.", muc="III.8",
               de_xuat="Bổ sung biên bản chạy thử đơn động, liên động và hồ sơ lắp đặt thiết bị (hoặc giải thích lý do không có).")
    hd = [r for r in by_muc.get("I.8", []) if re.search(r"hop dong", txt_rows[r["id"]])]
    co_tong_thau = bool(meta.get("tong_thau")) or vai_tro == "phu"
    hd_phu = [r for r in hd if re.search(r"thau phu|nha thau phu", txt_rows[r["id"]])]
    hd_chinh = [r for r in hd if re.search(r"tong thau|thau chinh|chu dau tu|\bcdt\b", txt_rows[r["id"]])]
    if (hd_phu or co_tong_thau) and not hd_chinh:
        _f(findings, "mid", "F22", "Danh mục chỉ thể hiện hợp đồng của nhà thầu (thầu phụ / dưới tổng thầu), chưa thấy hợp đồng tổng thầu / thầu chính",
           ("Có tổng thầu: " + meta["tong_thau"] + ". ") if meta.get("tong_thau") else "",
           dong=[r["id"] for r in hd], muc="I.8",
           de_xuat="Bổ sung hợp đồng giữa chủ đầu tư với tổng thầu / thầu chính làm căn cứ phạm vi gói thầu.")

    # ---------------- 3. mã VPĐT
    ma_map = OrderedDict()
    for r in rows:
        for x in r["ma"]:
            e = ma_map.setdefault(x, {"dong": [], "dong_ke_thua": [], "muc": set(), "noi_dung": []})
            e["dong"].append(r["id"])
            e["noi_dung"].append(r["noi_dung"][:90])
            if r.get("muc"):
                e["muc"].add(r["muc"])
        for x in r["ma_ke_thua"]:
            e = ma_map.setdefault(x, {"dong": [], "dong_ke_thua": [], "muc": set(), "noi_dung": []})
            e["dong_ke_thua"].append(r["id"])
            if r.get("muc"):
                e["muc"].add(r["muc"])
    if not cot_ma:
        _f(findings, "info", "F05", "Danh mục chưa thể hiện mã hồ sơ trên VPĐT (TEXO E-Office)",
           "Ghi nhận: hồ sơ chưa đăng tải hoặc danh mục không thể hiện đầy đủ – người đọc không truy được bản điện tử. "
           "Điều 28.4 NĐ 207 yêu cầu lưu trữ bản gốc và bản sao điện tử.",
           de_xuat="Thêm cột 'Mã TEXO-E' cho từng dòng (HS.yyyy.nnnn), mỗi thành phần hồ sơ một mã.")
    else:
        chi_tiet_khong_ma = [r for r in rows if _la_dong_chi_tiet(r) and not r["ma_hl"] and r.get("muc") != "T.9"]
        if chi_tiet_khong_ma:
            _f(findings, "info", "F05", f"{len(chi_tiet_khong_ma)} dòng hồ sơ chưa có mã VPĐT – chưa đăng tải hoặc chưa thể hiện",
               "Dòng: " + _fmt_ids([r["id"] for r in chi_tiet_khong_ma], 25),
               dong=[r["id"] for r in chi_tiet_khong_ma],
               de_xuat="Đăng tải và ghi mã HS cho từng dòng; hồ sơ chưa có thì ghi 'chưa có'.")
        for x, e in ma_map.items():
            codes = {c for c in e["muc"] if c and not c.startswith("T.9")}
            nhoms = {_nhom_pl(c) for c in codes}
            n_dong = len(e["dong"]) + len(e["dong_ke_thua"])
            e["gom"] = len(codes) >= 3 or (len(nhoms) >= 2 and len(codes) >= 2)
            if e["gom"]:
                _f(findings, "mid", "F06", f"Mã {x} gom {n_dong} dòng thuộc {len(codes)} mục PL VII khác nhau",
                   "Các mục: " + ", ".join(sorted(codes, key=lambda c: kb.UU_TIEN.index(c) if c in kb.UU_TIEN else 99)) +
                   ". Một file nén chung khiến người tra cứu phải tải về và mở toàn bộ mới tìm được tài liệu cần.",
                   dong=e["dong"] + e["dong_ke_thua"],
                   de_xuat="Tách hồ sơ theo từng mục PL VII (mỗi mục ít nhất một mã HS riêng).")
            elif len(e["dong"]) >= 2 and len(set(e["noi_dung"])) >= 2:
                _f(findings, "info", "F08", f"Mã {x} dùng chung cho {len(e['dong'])} dòng nội dung khác nhau",
                   " · ".join(sorted(set(e["noi_dung"])))[:300], dong=e["dong"],
                   de_xuat="Kiểm tra lại: có thể nhầm mã hoặc nên tách hồ sơ.")
    # định dạng mã
    sai_dd, thua_cach, vb_den = [], [], []
    for r in rows:
        raw = r.get("ma_raw") or ""
        if raw.strip() and not r["ma"]:
            sai_dd.append(r["id"])
        if raw and raw != raw.strip():
            thua_cach.append(r["id"])
        if any(x.startswith("VB") for x in r["ma"]):
            vb_den.append(r["id"])
    if sai_dd:
        _f(findings, "mid", "F07", f"{len(sai_dd)} ô mã VPĐT không đúng định dạng HS.yyyy.nnnn",
           "Dòng: " + _fmt_ids(sai_dd), dong=sai_dd, de_xuat="Sửa lại mã theo đúng mã trên VPĐT.")
    if thua_cach:
        _f(findings, "info", "F07", f"{len(thua_cach)} ô mã có khoảng trắng thừa ở đầu/cuối",
           "Dòng: " + _fmt_ids(thua_cach) + ". Không sai nội dung nhưng làm tra cứu/lọc tự động bị lệch.", dong=thua_cach,
           de_xuat="Xóa khoảng trắng thừa trong ô mã.")
    if vb_den:
        _f(findings, "info", "F07", f"{len(vb_den)} dòng dùng mã văn bản (VB …) thay cho mã hồ sơ (HS …)",
           "Dòng: " + _fmt_ids(vb_den) + ". Mã văn bản đến/đi truy được công văn nhưng không phải hồ sơ đã lập.", dong=vb_den,
           de_xuat="Nếu là thành phần hồ sơ hoàn thành, nên lập hồ sơ (HS) và dẫn mã HS.")

    # ---------------- 4. ngày tháng
    us, loi, tuong_lai, sau_nt, thieu_ngay_vb = [], [], [], [], []
    all_dates = []
    for r in rows:
        d, kieu = doc_ngay(r.get("ngay_obj") if r.get("ngay_obj") not in (None, "") else r.get("ngay_raw"))
        r["ngay_date"] = d
        if d:
            all_dates.append(d)
        if kieu == "us":
            us.append(r["id"])
        elif kieu == "loi":
            loi.append(r["id"])
        if d and d > hom_nay:
            tuong_lai.append(r["id"])
        if d and ngay_nt and d > ngay_nt and kieu != "my":
            sau_nt.append(r["id"])
        if r.get("muc") and kb.MUC_BY_CODE[r["muc"]]["hinh_thuc"] in ("VB", "PD") and r["so_vb"] and not r["ngay_raw"]:
            thieu_ngay_vb.append(r["id"])
    if not ngay_nt and all_dates and max(all_dates) < date(*kb.NGAY_HIEU_LUC_207):
        _f(findings, "info", "F13", f"Tài liệu muộn nhất ghi ngày {max(all_dates):%d/%m/%Y} (trước 01/7/2026)",
           "Nếu nghiệm thu diễn ra trước 01/7/2026 thì căn cứ là NĐ 06/2021 (Phụ lục VIb). Nhập ngày nghiệm thu để công cụ chấm đúng nghị định.")
    if us:
        _f(findings, "mid", "F09", f"{len(us)} ngày ghi theo kiểu tháng/ngày/năm (kiểu Mỹ)",
           "Dòng: " + _fmt_ids(us), dong=us, de_xuat="Thống nhất định dạng dd/mm/yyyy.")
    if loi:
        _f(findings, "mid", "F09", f"{len(loi)} ngày không hợp lệ", "Dòng: " + _fmt_ids(loi), dong=loi,
           de_xuat="Kiểm tra lại ngày ban hành.")
    if tuong_lai:
        _f(findings, "mid", "F09", f"{len(tuong_lai)} ngày ban hành muộn hơn hôm nay ({hom_nay:%d/%m/%Y})",
           "Dòng: " + _fmt_ids(tuong_lai) + ". Thường do gõ nhầm năm hoặc đảo ngày–tháng.", dong=tuong_lai,
           de_xuat="Sửa lại ngày.")
    if sau_nt:
        _f(findings, "mid", "F09", f"{len(sau_nt)} tài liệu có ngày sau ngày nghiệm thu ({ngay_nt:%d/%m/%Y})",
           "Dòng: " + _fmt_ids(sau_nt) + ". Tài liệu làm căn cứ nghiệm thu không thể ban hành sau ngày nghiệm thu.",
           dong=sau_nt, de_xuat="Hỏi đoàn: ký lùi ngày hay ghi nhầm ngày? Thống nhất lại mốc thời gian.")
    if thieu_ngay_vb:
        _f(findings, "info", "F09", f"{len(thieu_ngay_vb)} văn bản có số nhưng thiếu ngày ban hành",
           "Dòng: " + _fmt_ids(thieu_ngay_vb), dong=thieu_ngay_vb, de_xuat="Bổ sung ngày ban hành.")

    # ---------------- 5. chuỗi lần/đợt
    seq = defaultdict(list)
    for r in rows:
        m = re.search(r"^(.*?)\b(lan|dot)\s*(\d{1,3})\b", norm(r["noi_dung"]))
        if m:
            m2 = re.search(r"^(.*?)\b(lần|đợt)\s*\d{1,3}", r["noi_dung"], re.I)
            hien = (m2.group(1).strip() + " " + m2.group(2).lower()) if m2 else (m.group(1) + " " + m.group(2))
            key = (r["cha"], m.group(1).strip()[:50], hien)
            seq[key].append((int(m.group(3)), r))
    for (cha, _k, hien), lst in seq.items():
        nums = sorted({n for n, _ in lst})
        if len(nums) >= 2:
            gaps = [n for n in range(nums[0], nums[-1] + 1) if n not in nums]
            if gaps:
                _f(findings, "mid", "F10", f"Chuỗi “{hien} …” bị đứt quãng: thiếu {', '.join(map(str, gaps))}",
                   f"Có các lần: {', '.join(map(str, nums))} (dòng {_fmt_ids(r['id'] for _, r in lst)}).",
                   dong=[r["id"] for _, r in lst], de_xuat="Bổ sung hồ sơ lần còn thiếu hoặc giải thích lý do.")
        trong = [r for _, r in lst if not (r["ma_hl"] if r["ma"] else False) and not r["ngay_raw"] and not r["so_vb"] and not r["ma"]]
        if trong and len(trong) < len(lst):
            _f(findings, "mid", "F11", f"{len(trong)} dòng “{hien} …” được kê sẵn nhưng chưa có hồ sơ (trống ngày, mã)",
               "Dòng: " + _fmt_ids(r["id"] for r in trong), dong=[r["id"] for r in trong],
               de_xuat="Xóa dòng kê sẵn hoặc bổ sung hồ sơ, tránh hiểu nhầm là đã có.")
    khong_ten = [r["id"] for r in rows if not r["noi_dung"].strip() and (r["ma"] or r["so_vb"])]
    if khong_ten:
        _f(findings, "mid", "F11", f"{len(khong_ten)} dòng có mã/số hiệu nhưng không có tên hồ sơ",
           "Dòng: " + _fmt_ids(khong_ten), dong=khong_ten, de_xuat="Bổ sung tên hồ sơ cho dòng này.")

    # ---------------- 6. ngoài PL VII, chưa phân loại, bản gốc/sao
    t9 = by_muc.get("T.9", [])
    if t9:
        _f(findings, "info", "F14", f"{len(t9)} dòng là hồ sơ thanh toán/quyết toán/khối lượng – ngoài danh mục hồ sơ hoàn thành",
           "Dòng: " + _fmt_ids(r["id"] for r in t9), dong=[r["id"] for r in t9],
           de_xuat="Lưu thành bộ hồ sơ thanh toán riêng; danh mục hoàn thành chỉ giữ hồ sơ chất lượng.")
    chua_pl = [r for r in rows if not r.get("muc") and _la_dong_chi_tiet(r)]
    if chua_pl:
        _f(findings, "info", "F19", f"{len(chua_pl)} dòng công cụ chưa xếp được vào mục PL VII",
           "Dòng: " + _fmt_ids([r["id"] for r in chua_pl], 20) + ". Bật AI để phân loại bổ sung, hoặc bổ sung từ khóa vào bộ quy tắc.",
           dong=[r["id"] for r in chua_pl])
    if cot_tt:
        sao_quan_trong = [r["id"] for r in rows if r.get("muc") in ("III.13", "T.1", "I.8") and "sao" in norm(r["tinh_trang"])]
        if sao_quan_trong:
            _f(findings, "mid", "F15", f"{len(sao_quan_trong)} tài liệu chính chỉ là bản sao",
               "Dòng: " + _fmt_ids(sao_quan_trong) + ". Điều 28.4: hồ sơ hoàn thành lưu bản gốc (hoặc bản chính/bản sao hợp pháp).",
               dong=sao_quan_trong, de_xuat="Ghi rõ nơi lưu bản gốc hoặc bổ sung bản gốc.")
    elif info.get("kieu") != "BAO_CAO_DANG_TAI":
        _f(findings, "info", "F15", "Danh mục chưa có cột tình trạng (bản gốc / bản sao / bản điện tử)",
           "Điều 28.4 NĐ 207: hồ sơ hoàn thành lưu bằng bản gốc và bản sao điện tử.",
           de_xuat="Thêm cột 'Tình trạng' và 'Số trang/Quyển số' để người nhận biết hồ sơ nằm ở đâu.")

    # ---------------- 7. đối chiếu báo cáo đăng tải / danh sách VPĐT
    doi_chieu = {}
    ma_dm = set(ma_map.keys())
    if bc_dang_tai:
        bc_rows = gan_muc(bc_dang_tai["rows"])
        ma_bc = OrderedDict()
        for r in bc_rows:
            for x in r["ma"]:
                ma_bc.setdefault(x, []).append(r)
        chi_bc = [x for x in ma_bc if x not in ma_dm]
        chi_dm = [x for x in ma_dm if x not in ma_bc]
        doi_chieu["bao_cao"] = dict(chi_bc=[(x, ma_bc[x][0]["noi_dung"], ma_bc[x][0].get("muc")) for x in chi_bc],
                                    chi_dm=chi_dm, chung=[x for x in ma_bc if x in ma_dm])
        if chi_bc:
            _f(findings, "mid", "F16", f"{len(chi_bc)} mã có trong báo cáo đăng tải nhưng không có trong danh mục",
               "; ".join(f"{x} ({ma_bc[x][0]['noi_dung'][:50]})" for x in chi_bc[:10]),
               de_xuat="Đưa các hồ sơ này vào đúng mục của danh mục hoặc giải thích lý do không đưa.")
        if chi_dm:
            _f(findings, "info", "F16", f"{len(chi_dm)} mã trong danh mục không có trong báo cáo đăng tải",
               ", ".join(chi_dm[:15]), de_xuat="Cập nhật báo cáo đăng tải cho khớp.")
    if ds_vpdt:
        khong_ton_tai = [x for x in ma_dm if x not in ds_vpdt]
        doi_chieu["vpdt"] = dict(khong_ton_tai=khong_ton_tai, tong=len(ds_vpdt))
        if khong_ton_tai:
            _f(findings, "mid", "F16", f"{len(khong_ton_tai)} mã trong danh mục không tìm thấy trong danh sách xuất từ VPĐT",
               ", ".join(khong_ton_tai[:20]), de_xuat="Kiểm tra lại mã (gõ nhầm, hồ sơ thuộc dự án khác, hoặc chưa đăng tải).")

    findings.sort(key=lambda f: (SEV_ORDER[f["muc_do"]], f["ma_loi"]))
    for i, f in enumerate(findings, 1):
        f["stt"] = i

    # ---------------- 8. KPI
    ct_rows = [r for r in rows if _la_dong_chi_tiet(r)]
    co_ma_rows = [r for r in ct_rows if r["ma_hl"]]
    req = [it for it in items if it["yeu_cau"] == "B"]
    req_ok = [it for it in req if it["trang_thai"] in ("ok", "mid") and it["so_dong"]]
    kpi = dict(
        tong_dong=len(rows), dong_chi_tiet=len(ct_rows),
        muc_B=len(req), muc_B_co=len(req_ok), muc_B_dat=len([it for it in req if it["trang_thai"] == "ok"]),
        ty_le_B=round(100 * len(req_ok) / len(req)) if req else 0,
        so_ma=len(ma_map), so_ma_gom=len([e for e in ma_map.values() if e.get("gom")]),
        ty_le_co_ma=round(100 * len(co_ma_rows) / len(ct_rows)) if ct_rows else 0,
        high=len([f for f in findings if f["muc_do"] == "high"]),
        mid=len([f for f in findings if f["muc_do"] == "mid"]),
        info=len([f for f in findings if f["muc_do"] == "info"]),
        tu_ngay=min(all_dates).strftime("%d/%m/%Y") if all_dates else "",
        den_ngay=max(all_dates).strftime("%d/%m/%Y") if all_dates else "",
        chua_phan_loai=len(chua_pl),
    )
    if kpi["high"]:
        ket_luan = "CHƯA ĐỦ – còn mục cốt lõi chưa có trong danh mục, cần bổ sung trước khi trình ký."
        kl_sev = "high"
    elif kpi["mid"]:
        ket_luan = "CƠ BẢN CÓ – cần hoàn thiện thông tin (số/ngày văn bản, danh mục chi tiết, mã VPĐT) trước khi trình ký."
        kl_sev = "mid"
    else:
        ket_luan = "ĐỦ THEO DANH MỤC – các mục bắt buộc đều có dấu hiệu trong danh mục; vẫn cần mở quyển để kiểm tra nội dung."
        kl_sev = "ok"

    # câu hỏi kiểm tra theo mục (theo ghi chú chuyên môn của P.KT)
    it_by = {it["code"]: it for it in items}
    cau_hoi_muc = []
    for code, qs in kb.CAU_HOI_KT.items():
        if code in ("I", "III"):
            cau_hoi_muc.append(dict(code=code, ten=kb.NHOM[code], trang_thai="info", cau_hoi=qs))
            continue
        it = it_by.get(code)
        if not it or it["yeu_cau"] == "-":
            continue
        if code == "III.10đ" and not it_by["I.7"]["so_dong"]:
            continue
        if code == "III.10g" and not re.search(r"nha o|khu dan cu|do thi|ban hang|biet thu|lien ke|thap tang|ha tang ky thuat",
                                                norm(" ".join(str(v) for v in meta.values())) + " " + t_all):
            continue
        if code == "II.1" and not re.search(r"khao sat", norm(" ".join(str(v) for v in meta.values())) + " " + t_all) \
                and it["yeu_cau"] != "B":
            continue
        cau_hoi_muc.append(dict(code=code, ten=it["ten"], trang_thai=it["trang_thai"], cau_hoi=qs))
        it["cau_hoi_kt"] = qs

    cau_hoi = []
    for f in findings:
        if f["muc_do"] in ("high", "mid") and f.get("de_xuat") and f["de_xuat"] not in cau_hoi:
            cau_hoi.append(f["de_xuat"])

    return dict(meta=meta, info=info, loai_nt=loai_nt, loai_nt_label=kb.LOAI_NT.get(loai_nt, loai_nt),
                nghi_dinh=nghi_dinh, ngay_nt=ngay_nt, rows=rows, items=items, ma_map=ma_map, findings=findings,
                kpi=kpi, ket_luan=ket_luan, ket_luan_sev=kl_sev, cau_hoi=cau_hoi, cau_hoi_muc=cau_hoi_muc,
                vai_tro=vai_tro, doi_chieu=doi_chieu,
                warnings=doc.get("warnings", []))
