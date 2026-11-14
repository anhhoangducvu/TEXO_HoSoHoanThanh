# -*- coding: utf-8 -*-
"""Phiếu vòng 1 (kiểm tra đầu vào) và vòng 2 (rà soát sơ bộ) hồ sơ chất lượng – Word A4 theo mẫu trình bày TEXO.
Vòng 3 dùng phiếu đầy đủ (report_docx.py) và Excel (report_xlsx.py)."""
import io
from datetime import date

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from . import kb
from . import texo_docx as K
from .vong import TRA_LAI, KL_TRA_LAI, KL_LUU_Y, V2_THIEU, V2_LAM_RO, GOI_Y_GUI_LAI

FOOTER = "Tài liệu nội bộ · Kiểm tra hồ sơ chất lượng dự án · Người xây dựng: Hoàng Đức Vũ – Trưởng phòng Kỹ thuật"
K.SEV.update({"Trả lại": ("🔴", K.C["red"], K.C["redBg"]), "Lưu ý": ("🟠", K.C["orange"], K.C["orangeBg"]),
              "Thiếu": ("🔴", K.C["red"], K.C["redBg"]), "Cần làm rõ": ("🟠", K.C["orange"], K.C["orangeBg"]),
              "Có": ("🟢", K.C["green"], K.C["greenBg"]), "Chưa thấy": ("🟠", K.C["orange"], K.C["orangeBg"])})
V1_COLOR = {KL_TRA_LAI: "red", KL_LUU_Y: "orange"}
V2_COLOR = {V2_THIEU: "red", V2_LAM_RO: "orange"}
NHAC_PHAP_LY = ("Văn bản pháp lý, tiêu chuẩn dẫn trong hồ sơ: kiểm tra hiệu lực bản mới nhất bằng công cụ "
                "TEXO Legal Reviewer trước khi trình ký.")


def _doc(sub):
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name, st.font.size = K.FONT, Pt(12)
    content = K.setup_section(doc.sections[0], "A4P", "KIỂM TRA HỒ SƠ CHẤT LƯỢNG DỰ ÁN", sub, FOOTER)
    return doc, content


def _title(doc, small, big, info, d):
    K.para(doc, small, 11, b=True, c=K.C["blue"], align=WD_ALIGN_PARAGRAPH.CENTER, before=4, after=3)
    K.para(doc, big, 17, b=True, c=K.C["navy"], align=WD_ALIGN_PARAGRAPH.CENTER, after=4)
    dong = " – ".join(x for x in (info.get("du_an"), info.get("nha_thau")) if x)
    if dong:
        K.para(doc, dong, 12.5, b=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=4)
    K.para(doc, f"Hồ sơ: {info.get('ho_so', '')} · Ngày kiểm tra: {d:%d/%m/%Y}", 10.5, i=True, c=K.C["grey"],
           align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
    rule = K.para(doc, "", after=8)
    K._pborder(rule, "bottom", K.C["blue"], 10, 1)


def _sign(doc, content, info, d):
    K.spacer(doc, 8)
    K.para(doc, NHAC_PHAP_LY, 9.5, i=True, c=K.C["grey"], after=6)
    ben = [["NGƯỜI KIỂM TRA", info.get("nguoi", "")], ["TRƯỞNG PHÒNG KỸ THUẬT", "Hoàng Đức Vũ"]]
    K.signature_block(doc, content, d, ben, info.get("noi_nhan") or
                      ["Trung tâm, đoàn TVGS (để t/h);", "Nhà thầu (qua đoàn TVGS);", "Lưu: P.KT."])


def _nhan_dien(v1):
    nd = v1.nhan_dien or {}
    if not nd:
        return []
    out = [("Nhà thầu", nd.get("nha_thau") or "– chưa thể hiện –"),
           ("Phạm vi (gói thầu / hạng mục)", nd.get("pham_vi") or "– chưa thể hiện –"),
           ("Vai trò gợi ý", ("Thầu phụ" if nd.get("vai_tro") == "phu" else "Tổng thầu / thầu chính") + f" ({nd.get('ly_do_vai_tro', '')})"),
           ("Quy mô gợi ý", kb.QUY_MO_NGAN.get(nd.get("quy_mo"), "") + f" ({nd.get('ly_do_quy_mo', '')})"),
           ("Loại nghiệm thu gợi ý", kb.LOAI_NT.get(nd.get("loai_goi_y"), "– chưa rõ, người kiểm tra chọn –")),
           ("Số dòng hồ sơ đọc được", str(nd.get("so_dong", "")))]
    return out


def build_v1(v1, info):
    d = info.get("ngay") or date.today()
    doc, content = _doc("Vòng 1 – kiểm tra đầu vào")
    _title(doc, "PHÒNG KỸ THUẬT · VÒNG 1", "PHIẾU KIỂM TRA ĐẦU VÀO HỒ SƠ CHẤT LƯỢNG", info, d)
    tl = [m for m in v1.muc if m["muc"] == TRA_LAI]
    ly = [m for m in v1.muc if m["muc"] != TRA_LAI]
    K.kpi_row(doc, [(v1.ket_luan, "Kết luận", "kiểm tra hình thức file", V1_COLOR.get(v1.ket_luan, "green")),
                    (f"{len(v1.tep_doc_duoc)}/{len(v1.tep)}", "File đọc được", "đưa vào kiểm tra", "navy"),
                    (str(len(tl)), "Lý do trả lại", "phải xử lý", "red"),
                    (str(len(ly)), "Lưu ý", "nên xử lý", "orange")], content, value_size=16)
    K.spacer(doc, 8)
    if v1.ket_luan == KL_TRA_LAI:
        body = ["Bộ hồ sơ chưa đạt yêu cầu đầu vào tối thiểu nên chưa rà soát nội dung. Đề nghị gửi lại theo các điểm dưới đây."]
    elif v1.ket_luan == KL_LUU_Y:
        body = ["Bộ hồ sơ đọc được, đã chuyển sang rà soát sơ bộ. Có một số điểm nên xử lý để lần sau kiểm tra nhanh và đủ hơn."]
    else:
        body = ["Bộ hồ sơ đạt yêu cầu đầu vào, đã chuyển sang rà soát sơ bộ."]
    K.callout(doc, "KẾT LUẬN", body, content, color=V1_COLOR.get(v1.ket_luan, "green"))
    K.h1(doc, "I. CÁC FILE ĐÃ NHẬN")
    w = [560, 3790, 800, 900, 1500, 1521]
    w[-1] += content - sum(w)
    rows = []
    for i, t in enumerate(v1.tep, 1):
        ct = []
        if t.get("so_trang"):
            ct.append(f"{t['so_trang']} trang" + (f", {t['trang_scan']} trang scan" if t.get("trang_scan") else ""))
        if t.get("so_sheet"):
            ct.append(f"{t['so_sheet']} sheet")
        if t.get("anh"):
            ct.append(f"{t['anh']} ảnh")
        rows.append([str(i), t["ten"], t["dinh_dang"], f"{t['mb']} MB", ", ".join(ct) or "—",
                     "Trả lại" if t["ket_luan"] == KL_TRA_LAI else ("Lưu ý" if t["ket_luan"] == KL_LUU_Y else "Có")])
    K.data_table(doc, w, ["TT", "File", "Định dạng", "Dung lượng", "Cấu trúc", "Kết luận"], rows, size=9.5,
                 sev_col=5, center_cols=(0, 2, 3))
    if v1.muc:
        K.h1(doc, "II. CÁC ĐIỂM CẦN XỬ LÝ")
        w = [560, 1250, 3890, 3371]
        w[-1] += content - sum(w)
        K.data_table(doc, w, ["TT", "Mức", "Nội dung", "Cách xử lý"],
                     [[str(i), m["muc"], ([{"text": m["tep"], "b": True, "size": 9}] if m.get("tep") else []) +
                       [m["noi_dung"]], m["xu_ly"]] for i, m in enumerate(tl + ly, 1)],
                     size=10, sev_col=1, center_cols=(0,))
    nd = _nhan_dien(v1)
    if nd:
        K.h1(doc, "III. NHẬN DIỆN SƠ BỘ")
        K.meta_table(doc, nd, content, label_ratio=0.32)
        K.para(doc, "Nhận diện tự động, người kiểm tra xác nhận lại trước khi rà soát vòng 2.", 9.5, i=True, c=K.C["grey"],
               before=3)
    if v1.ket_luan == KL_TRA_LAI:
        K.h1(doc, "IV. YÊU CẦU TỐI THIỂU KHI GỬI LẠI")
        for x in GOI_Y_GUI_LAI:
            K.bullet(doc, x)
    _sign(doc, content, info, d)
    doc.core_properties.author = "Hoàng Đức Vũ"
    doc.core_properties.title = "Phiếu kiểm tra đầu vào hồ sơ chất lượng"
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def build_v2(v2, v1, info):
    d = info.get("ngay") or date.today()
    doc, content = _doc("Vòng 2 – rà soát sơ bộ")
    _title(doc, "PHÒNG KỸ THUẬT · VÒNG 2", "PHIẾU RÀ SOÁT SƠ BỘ HỒ SƠ CHẤT LƯỢNG", info, d)
    tp = v2.thanh_phan
    n_co = len([c for c in tp if c["trang_thai"] == "co"])
    n_thieu = len([c for c in tp if c["trang_thai"] == "thieu" and c["chan"]])
    K.kpi_row(doc, [(f"{n_co}/{len(tp)}", "Thành phần cơ bản", "đã có trong danh mục", "navy"),
                    (str(n_thieu), "Thiếu cơ bản", "bổ sung trước", "red"),
                    (str(len(tp) - n_co - n_thieu), "Cần làm rõ", "hỏi lại đoàn", "orange"),
                    (str(len(v2.pham_vi_v3.get("B", []))), "Mục xét ở vòng 3", "theo quy mô nhà thầu", "blue")], content,
              value_size=18)
    K.spacer(doc, 8)
    body = [f"{v2.ket_luan}. {v2.nhan_xet}"]
    K.callout(doc, "KẾT LUẬN SƠ BỘ", body, content, color=V2_COLOR.get(v2.ket_luan, "green"))
    K.h1(doc, "I. PHẠM VI RÀ SOÁT")
    pairs = [("Loại nghiệm thu", kb.LOAI_NT.get(v2.loai, v2.loai)),
             ("Nhà thầu", (info.get("nha_thau") or "– chưa thể hiện –")),
             ("Vai trò", "Thầu phụ" if v2.vai_tro == "phu" else "Tổng thầu / thầu chính"),
             ("Quy mô – phạm vi kiểm tra", kb.QUY_MO.get(v2.quy_mo, ""))]
    if v1 is not None:
        pairs.append(("Kiểm tra đầu vào (vòng 1)", v1.ket_luan + (f" – {len(v1.muc)} lưu ý" if v1.muc else "")))
    pairs += [(k, str(x)) for k, x in v2.thong_ke.items()]
    K.meta_table(doc, pairs, content, label_ratio=0.34)
    K.h1(doc, "II. THÀNH PHẦN HỒ SƠ CƠ BẢN")
    w = [560, 3490, 1300, 3721]
    w[-1] += content - sum(w)
    rows = []
    for i, c in enumerate(tp, 1):
        tt = {"co": "Có", "thieu_dm": "Cần làm rõ"}.get(c["trang_thai"], "Thiếu" if c["chan"] else "Chưa thấy")
        if c["trang_thai"] == "co":
            ghi = (f"{c['so_dong']} dòng" + (f", {c['so_chi_tiet']} hồ sơ chi tiết" if c["danh_muc"] else "") +
                   (" · " + "; ".join(c["mau"][:2]) if c["mau"] else ""))
        elif c["trang_thai"] == "thieu_dm":
            ghi = "Mới có tên quyển / một dòng: " + "; ".join(c["mau"][:2])
        else:
            ghi = c["cau_hoi"]
        rows.append([str(i), [{"text": c["ten"], "b": True}] + ([{"text": "Bắt buộc", "i": True, "c": K.C["grey"], "size": 8.5}]
                                                                 if c["chan"] else []), tt, ghi])
    K.data_table(doc, w, ["TT", "Thành phần", "Hiện trạng", "Ghi nhận / đề nghị"], rows, size=9.5, sev_col=2, center_cols=(0,))
    if v2.cau_hoi:
        K.h1(doc, "III. ĐỀ NGHỊ ĐOÀN TƯ VẤN BỔ SUNG / LÀM RÕ")
        for i, q in enumerate(v2.cau_hoi, 1):
            K.para(doc, f"{i}. {q}", 11.5, after=2)
    K.h1(doc, ("IV" if v2.cau_hoi else "III") + ". BƯỚC TIẾP THEO")
    if v2.ket_luan == V2_THIEU:
        K.bullet(doc, "Đoàn bổ sung các thành phần còn thiếu rồi gửi lại; P.KT kiểm tra chi tiết (vòng 3) sau khi đủ hồ sơ cơ bản.")
    else:
        K.bullet(doc, f"Vòng 3 đối chiếu chi tiết {len(v2.pham_vi_v3.get('B', []))} mục bắt buộc và "
                      f"{len(v2.pham_vi_v3.get('D', []))} mục đối chiếu theo Phụ lục VII: " + ", ".join(v2.pham_vi_v3.get("B", [])) + ".")
    if v2.quy_mo != "lon":
        K.bullet(doc, "Nhà thầu không phải tổng thầu / thầu chính: không yêu cầu lập lại danh mục đủ Phụ lục VII; hồ sơ pháp lý dự án "
                      "(chủ trương, phê duyệt dự án, đất đai, đấu nối, quy hoạch) do chủ đầu tư tập hợp.")
    _sign(doc, content, info, d)
    doc.core_properties.author = "Hoàng Đức Vũ"
    doc.core_properties.title = "Phiếu rà soát sơ bộ hồ sơ chất lượng"
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()
