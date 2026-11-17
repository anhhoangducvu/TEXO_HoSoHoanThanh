# -*- coding: utf-8 -*-
"""
Kiểm tra hồ sơ chất lượng theo 3 vòng – dùng chung cho app Streamlit và skill texo-kiemtra-hoso-chatluong.

Vòng 1 – Kiểm tra đầu vào: chỉ đọc "vỏ" file (định dạng, dung lượng, file hỏng / đặt mật khẩu, PDF ảnh scan,
         ảnh chụp dán vào Word/Excel, số trang) rồi nhận diện sơ bộ: loại tài liệu, nhà thầu, thầu chính hay thầu phụ,
         nhà thầu lớn / hạng mục / nhỏ, loại nghiệm thu. Kết luận ĐẠT / ĐẠT CÓ LƯU Ý / TRẢ LẠI.
         Bộ hồ sơ nhiều file: file không đọc được bị loại ra và ghi rõ, các file còn lại vẫn đi tiếp.
Vòng 2 – Rà soát sơ bộ: chỉ tìm các thành phần cốt lõi (hợp đồng, nhân sự, biên bản nghiệm thu, danh mục NT vật liệu,
         NT công việc, hoàn công; thầu phụ thêm chấp thuận thầu phụ và HĐ thầu chính – CĐT; nhà thầu lớn thêm GPXD,
         thiết kế duyệt). Thiếu thành phần cơ bản thì đề nghị bổ sung trước khi kiểm tra chi tiết.
Vòng 3 – Kiểm tra chi tiết: checker.kiem_tra() đối chiếu Phụ lục VII theo phạm vi của quy mô nhà thầu.
"""
import io
import re
import zipfile
from dataclasses import dataclass, field, asdict

from . import kb
from . import cot_loi

KL_DAT, KL_LUU_Y, KL_TRA_LAI = "ĐẠT", "ĐẠT CÓ LƯU Ý", "TRẢ LẠI"
TRA_LAI, LUU_Y = "Trả lại", "Lưu ý"
V2_THIEU, V2_LAM_RO, V2_DU = "THIẾU HỒ SƠ CƠ BẢN", "ĐỦ HỒ SƠ CƠ BẢN – CÒN ĐIỂM CẦN LÀM RÕ", "ĐỦ HỒ SƠ CƠ BẢN"
V2_SEV = {V2_THIEU: "high", V2_LAM_RO: "mid", V2_DU: "ok"}
V1_SEV = {KL_TRA_LAI: "high", KL_LUU_Y: "mid", KL_DAT: "ok"}

GOI_Y_GUI_LAI = [
    "Danh mục gửi bản Word (.docx) / Excel (.xlsx) gốc, hoặc PDF xuất trực tiếp từ Word/Excel (bôi đen được chữ).",
    "Bản scan có chữ ký, đóng dấu nộp kèm để lưu; công cụ kiểm tra đọc bản gốc.",
    "Chỉ cần nộp danh mục (mục lục) để kiểm tra, không cần nộp cả quyển hồ sơ scan.",
    "File cũ .doc / .xls: mở bằng Word/Excel, lưu lại thành .docx / .xlsx.",
    "Mỗi file dưới 30 MB; danh mục rời theo loại / theo đợt đều được.",
]


@dataclass
class V1:
    ket_luan: str = KL_DAT
    muc: list = field(default_factory=list)       # dict(muc, tep, noi_dung, xu_ly)
    tep: list = field(default_factory=list)       # dict(ten, dinh_dang, mb, so_trang, trang_scan, ket_luan, doc_duoc)
    nhan_dien: dict = field(default_factory=dict)  # vai_tro, quy_mo, nha_thau, pham_vi, ly_do…, loai_goi_y, kieu
    ocr: bool = False

    @property
    def tra_lai(self):
        return self.ket_luan == KL_TRA_LAI

    @property
    def tep_doc_duoc(self):
        return [t["ten"] for t in self.tep if t["doc_duoc"]]

    def to_dict(self):
        return asdict(self)


# ----------------------------------------------------------------------------- vòng 1: vỏ file
def _mb(n):
    return round(n / 1048576, 2)


def _kiem_ooxml(name, data, ext, add, ts):
    if data[:4] == b"\xd0\xcf\x11\xe0":
        add(TRA_LAI, "File đặt mật khẩu (mã hóa) hoặc là file đời cũ đổi đuôi – công cụ không mở được.",
            "Gỡ mật khẩu (File › Info › Protect › bỏ mật khẩu) hoặc lưu lại đúng định dạng .docx/.xlsx rồi gửi lại.")
        return
    if not zipfile.is_zipfile(io.BytesIO(data)):
        add(TRA_LAI, "File bị hỏng hoặc không đúng định dạng Office (không mở được).", "Mở lại bằng Word/Excel, lưu thành file mới rồi gửi lại.")
        return
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        names = z.namelist()
    except Exception:
        add(TRA_LAI, "File bị hỏng (không giải nén được).", "Mở lại bằng Word/Excel, lưu thành file mới rồi gửi lại.")
        return
    media = [n for n in names if "/media/" in n]
    ts["anh_trong_file"] = len(media)
    if ext == "docx":
        try:
            xml = z.read("word/document.xml").decode("utf-8", "ignore")
        except KeyError:
            add(TRA_LAI, "File Word thiếu nội dung chính (word/document.xml).", "Lưu lại file bằng Word rồi gửi lại.")
            return
        chu = sum(len(x) for x in re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", xml))
        bang = xml.count("<w:tbl>")
        ts["so_ky_tu"], ts["so_bang"] = chu, bang
        if chu < kb.VONG1["word_chu_toi_thieu"] and media:
            add(TRA_LAI, f"File Word chỉ chứa ảnh chụp / ảnh scan ({len(media)} ảnh, {chu} ký tự chữ) – không đọc được nội dung.",
                "Gửi bản Word gốc của danh mục (gõ chữ, có bảng), không chèn ảnh chụp.")
        elif chu < 40:
            add(TRA_LAI, "File Word gần như không có chữ.", "Kiểm tra lại file gửi lên.")
        elif not bang:
            add(LUU_Y, "File Word không có bảng – công cụ đọc theo từng dòng chữ, độ chính xác thấp hơn.",
                "Nên lập danh mục dạng bảng: STT, tên hồ sơ, số hiệu, ngày, đơn vị ban hành, mã VPĐT.")
    else:
        if any(n.endswith("vbaProject.bin") for n in names):
            add(LUU_Y, "File Excel có macro (VBA) – công cụ bỏ qua macro, chỉ đọc giá trị ô.",
                "Danh mục không cần macro; nên lưu .xlsx thường.")
        wb = ""
        try:
            wb = z.read("xl/workbook.xml").decode("utf-8", "ignore")
            n_sheet = len(re.findall(r"<sheet\s", wb))
        except KeyError:
            n_sheet = 0
        ts["so_sheet"] = n_sheet
        chu = 0
        if "xl/sharedStrings.xml" in names:
            chu = sum(len(x) for x in re.findall(r"<t(?:\s[^>]*)?>([^<]*)</t>",
                                                 z.read("xl/sharedStrings.xml").decode("utf-8", "ignore")))
        ts["so_ky_tu"] = chu
        _kiem_excel_cau_truc(z, names, wb, add, ts)
        if n_sheet > kb.VONG1["so_sheet_luu_y"]:
            add(LUU_Y, f"File có {n_sheet} sheet – nên chọn đúng sheet danh mục khi kiểm tra.", "Xóa sheet nháp, sheet không dùng.")
        if chu < 40 and media:
            add(TRA_LAI, "File Excel chỉ chứa ảnh chụp / ảnh scan – không có chữ trong ô.", "Gửi bản Excel gốc gõ chữ trong ô.")


def _cot_so(ref):
    col = re.match(r"([A-Z]+)", ref or "")
    n = 0
    for ch in (col.group(1) if col else ""):
        n = n * 26 + ord(ch) - 64
    return n


def _kiem_excel_cau_truc(z, names, wb_xml, add, ts):
    """Vùng dữ liệu ảo, tên vùng (Name) rác, liên kết ngoài – nguyên nhân hay gặp làm file nặng, máy chủ treo."""
    sheet_xml = [n for n in names if n.startswith("xl/worksheets/") and n.endswith(".xml")]
    tong = sum(z.getinfo(n).file_size for n in sheet_xml)
    ts["xml_mb"] = _mb(tong)
    if tong > kb.VONG1["excel_xml_tra_lai_mb"] * 1048576:
        add(TRA_LAI, f"Nội dung các sheet giải nén ra {_mb(tong)} MB – quá lớn so với một danh mục.",
            "Chỉ giữ sheet danh mục; xóa sheet tính toán, ảnh, dữ liệu thừa rồi lưu lại.")
        return
    ao = []
    for n in sheet_xml:
        with z.open(n) as f:
            head = f.read(4096).decode("utf-8", "ignore")
        m = re.search(r'<dimension ref="[A-Z]+\d+:([A-Z]+)(\d+)"', head)
        if m:
            cot, dong = _cot_so(m.group(1)), int(m.group(2))
            if cot > kb.VONG1["excel_cot_ao"] or dong > kb.VONG1["excel_dong_ao"]:
                ao.append(f"{m.group(1)}{dong}")
    if ao:
        add(LUU_Y, "File Excel có vùng định dạng thừa kéo tới ô " + ", ".join(ao[:3]) +
            " (hàng nghìn cột/dòng trống) – nhiều máy mở rất chậm; công cụ đã bỏ qua phần thừa.",
            "Xóa các cột/dòng trống thừa bên phải và bên dưới bảng (chọn cột → Delete), lưu lại.")
    n_name = len(re.findall(r"<definedName\s", wb_xml or ""))
    if n_name > kb.VONG1["excel_ten_vung"]:
        add(LUU_Y, f"File Excel chứa {n_name:,} tên vùng (Name) rác do sao chép qua nhiều file.".replace(",", "."),
            "Formulas › Name Manager: lọc tên lỗi (#REF!) và xóa; hoặc dán giá trị bảng sang file mới.")
    ext = [n for n in names if n.startswith("xl/externalLinks/") and n.endswith(".xml")]
    if ext:
        add(LUU_Y, f"File Excel liên kết tới {len(ext)} file bên ngoài (công thức trỏ sang máy khác).",
            "Data › Edit Links › Break Link, hoặc dán giá trị trước khi gửi.")


def _kiem_pdf(data, add, ts, ocr_ok, ocr):
    import pdfplumber
    try:
        pdf = pdfplumber.open(io.BytesIO(data))
    except Exception as e:
        msg = str(e).lower()
        if "password" in msg or "encrypt" in msg:
            add(TRA_LAI, "PDF đặt mật khẩu – không mở được.", "Gỡ mật khẩu rồi gửi lại.")
        else:
            add(TRA_LAI, "PDF bị hỏng – không mở được.", "Xuất lại PDF hoặc gửi bản Word/Excel gốc.")
        return False
    with pdf:
        n = len(pdf.pages)
        ts["so_trang"] = n
        quet = min(n, kb.VONG1["pdf_trang_quet_toi_da"])
        scan = []
        for i in range(quet):
            try:
                c = len(pdf.pages[i].chars)
            except Exception:
                c = 0
            if c < kb.VONG1["chu_toi_thieu_moi_trang"]:
                scan.append(i + 1)
    ts["trang_scan"] = len(scan)
    ts["trang_da_quet"] = quet
    if n > kb.VONG1["pdf_trang_tra_lai"]:
        add(TRA_LAI, f"PDF {n} trang – có vẻ là cả quyển hồ sơ, không phải danh mục.",
            "Chỉ nộp phần danh mục (mục lục) để kiểm tra; cả quyển đăng tải lên VPĐT theo từng mã HS.")
        return False
    if n > kb.VONG1["pdf_trang_luu_y"]:
        add(LUU_Y, f"PDF {n} trang – dài hơn một danh mục thông thường.", "Nên tách riêng phần danh mục để kiểm tra nhanh hơn.")
    if scan and len(scan) == quet:
        if ocr and ocr_ok:
            add(LUU_Y, f"PDF ảnh scan ({n} trang) – sẽ đọc bằng OCR {min(n, kb.VONG1['ocr_trang_toi_da'])} trang đầu, "
                       "độ chính xác thấp, phải đối chiếu lại.",
                "Lần sau gửi kèm bản Word/Excel gốc của danh mục.")
            return True
        add(TRA_LAI, f"PDF ảnh scan ({n} trang, không có lớp chữ) – công cụ không đọc được.",
            "Gửi bản Word/Excel gốc của danh mục hoặc PDF xuất trực tiếp từ Word/Excel; bản scan có chữ ký nộp kèm để lưu."
            + (" (Máy chủ có OCR: bật “Thử đọc bằng OCR” để đọc tạm.)" if ocr_ok else ""))
        return False
    if scan:
        ds = ", ".join(map(str, scan[:12])) + ("…" if len(scan) > 12 else "")
        add(LUU_Y, f"{len(scan)}/{quet} trang là ảnh scan (trang {ds}) – phần này công cụ không đọc được.",
            "Phần danh mục nằm ở trang scan cần gửi lại bản có chữ.")
    return True


def kiem_tra_tep(name, data, ocr=False, ocr_ok=False):
    """Kiểm tra vỏ một file. Trả (dict tệp, [mục])."""
    ext = name.lower().rsplit(".", 1)[-1] if "." in name else ""
    mb = _mb(len(data))
    out = []
    ts = {}

    def add(level, nd, xl):
        out.append(dict(muc=level, tep=name, noi_dung=nd, xu_ly=xl))

    if not data:
        add(TRA_LAI, "File rỗng (0 byte).", "Gửi lại file.")
    elif ext in kb.VONG1["dinh_dang_cu"]:
        add(TRA_LAI, f"File .{ext} đời cũ (Office 97-2003) – công cụ chưa đọc.",
            f"Mở bằng {'Word' if ext == 'doc' else 'Excel'}, chọn Save As › .{ext}x rồi gửi lại.")
    elif ext not in kb.VONG1["dinh_dang_doc"]:
        add(TRA_LAI, f"Định dạng .{ext or '?'} không phải danh mục đọc được (ảnh, file nén, bản vẽ…).",
            "Gửi danh mục dạng .docx, .xlsx hoặc PDF có chữ; ảnh và file nén đăng tải lên VPĐT.")
    else:
        if mb > kb.VONG1["dung_luong_tra_lai_mb"]:
            add(TRA_LAI, f"File nặng {mb} MB – vượt {kb.VONG1['dung_luong_tra_lai_mb']} MB.",
                "Danh mục chỉ cần vài trang; tách bỏ phần hồ sơ scan đi kèm, nén ảnh hoặc chia file.")
        elif mb > kb.VONG1["dung_luong_luu_y_mb"]:
            add(LUU_Y, f"File nặng {mb} MB – danh mục thường dưới 2 MB.", "Kiểm tra xem có chèn ảnh scan, ảnh chụp không.")
        if not any(x["muc"] == TRA_LAI for x in out):
            if ext in ("docx", "xlsx", "xlsm"):
                _kiem_ooxml(name, data, ext, add, ts)
            elif ext == "pdf":
                _kiem_pdf(data, add, ts, ocr_ok, ocr)
    kl = KL_TRA_LAI if any(x["muc"] == TRA_LAI for x in out) else (KL_LUU_Y if out else KL_DAT)
    tep = dict(ten=name, dinh_dang=ext.upper(), mb=mb, so_trang=ts.get("so_trang"), trang_scan=ts.get("trang_scan"),
               so_sheet=ts.get("so_sheet"), anh=ts.get("anh_trong_file"), ket_luan=kl, doc_duoc=kl != KL_TRA_LAI)
    return tep, out


def vong1(files, ocr=False):
    """files = [(tên, bytes)] → V1 (chỉ vỏ file). Gọi tiếp vong1_noi_dung(v1, doc) sau khi đọc danh mục."""
    ocr_ok = False
    if ocr:
        from . import ocr as _ocr
        ocr_ok = _ocr.san_sang()[0]
    v = V1(ocr=bool(ocr and ocr_ok))
    for name, data in files:
        t, m = kiem_tra_tep(name, data, ocr=ocr, ocr_ok=ocr_ok)
        v.tep.append(t)
        v.muc += m
    _chot_v1(v)
    return v


def _chot_v1(v):
    doc_duoc = [t for t in v.tep if t["doc_duoc"]]
    if not doc_duoc:
        v.ket_luan = KL_TRA_LAI
    elif v.muc:
        v.ket_luan = KL_LUU_Y
        loai = [t["ten"] for t in v.tep if not t["doc_duoc"]]
        if loai and not any(m.get("tong_hop") for m in v.muc):
            v.muc.insert(0, dict(muc=LUU_Y, tep="", tong_hop=True,
                                 noi_dung=f"{len(loai)}/{len(v.tep)} file không đọc được, đã loại khỏi lần kiểm tra này: " + "; ".join(loai),
                                 xu_ly="Các file còn lại vẫn được kiểm tra; đề nghị gửi lại bản đọc được của những file trên."))
    else:
        v.ket_luan = KL_DAT


def vong1_noi_dung(v, doc, ten_file=""):
    """Sau khi đọc được danh mục: soát nội dung tối thiểu và nhận diện nhà thầu, loại nghiệm thu."""
    from .parser import doan_loai_nt
    if doc is None and not v.tep_doc_duoc:
        return v  # đã trả lại ở bước kiểm tra file
    if doc is None or not doc.get("rows"):
        v.muc.append(dict(muc=TRA_LAI, tep="", noi_dung="Không nhận được dòng hồ sơ nào trong danh mục.",
                          xu_ly="Lập danh mục dạng bảng: STT, tên hồ sơ, số hiệu, ngày, đơn vị ban hành, mã VPĐT."))
        v.ket_luan = KL_TRA_LAI
        return v
    kieu = doc.get("info", {}).get("kieu")
    if kieu == "BAO_CAO_DANG_TAI":
        v.muc.append(dict(muc=LUU_Y, tep="", noi_dung="Tài liệu là báo cáo đăng tải VPĐT nội bộ, chưa phải danh mục hồ sơ.",
                          xu_ly="Gửi kèm danh mục hồ sơ của nhà thầu; báo cáo đăng tải dùng để đối chiếu mã."))
        if v.ket_luan == KL_DAT:
            v.ket_luan = KL_LUU_Y
    nd = cot_loi.nhan_dien_nha_thau(doc, ten_file)
    nd["loai_goi_y"] = doan_loai_nt(doc.get("meta", {}), (ten_file or "").replace("_", " ") + " " + str(doc.get("text", "")))
    nd["kieu"] = kieu
    nd["so_dong"] = len([r for r in doc["rows"] if not r.get("la_tep")])
    nd["du_an"] = doc.get("meta", {}).get("du_an", "")
    v.nhan_dien = nd
    return v


# ----------------------------------------------------------------------------- vòng 2: thành phần cốt lõi
@dataclass
class V2:
    ket_luan: str = V2_DU
    loai: str = "GD"
    vai_tro: str = "chinh"
    quy_mo: str = "lon"
    thanh_phan: list = field(default_factory=list)
    thong_ke: dict = field(default_factory=dict)
    cau_hoi: list = field(default_factory=list)
    pham_vi_v3: dict = field(default_factory=dict)
    nhan_xet: str = ""

    @property
    def sev(self):
        return V2_SEV.get(self.ket_luan, "mid")

    def to_dict(self):
        return asdict(self)


def vong2(doc, loai="GD", vai_tro="chinh", quy_mo="lon"):
    from .checker import gan_muc, _la_dong_chi_tiet
    rows = gan_muc(doc["rows"])
    tp = cot_loi.tim_thanh_phan(rows, doc.get("tep"), loai, vai_tro, quy_mo)
    v = V2(loai=loai, vai_tro=vai_tro, quy_mo=quy_mo, thanh_phan=tp)
    ct = [r for r in rows if _la_dong_chi_tiet(r)]
    co_ma = [r for r in ct if r.get("ma") or r.get("ma_ke_thua")]
    v.thong_ke = {"Số danh mục (file / sheet)": len([t for t in doc.get("tep") or [] if t.get("loai") != "bao_cao_dang_tai"]) or 1,
                  "Dòng hồ sơ chi tiết": len(ct),
                  "Dòng có mã VPĐT": f"{round(100 * len(co_ma) / len(ct)) if ct else 0}%",
                  "Thành phần cốt lõi có": f"{len([c for c in tp if c['trang_thai'] == 'co'])}/{len(tp)}"}
    thieu_chan = [c for c in tp if c["chan"] and c["trang_thai"] == "thieu"]
    lam_ro = [c for c in tp if c["trang_thai"] != "co" and c not in thieu_chan]
    for c in tp:
        if c["trang_thai"] == "thieu":
            v.cau_hoi.append(c["cau_hoi"])
        elif c["trang_thai"] == "thieu_dm":
            v.cau_hoi.append(f"{c['ten']}: mới có tên quyển / một dòng, chưa có danh mục chi tiết – đề nghị liệt kê từng "
                             "biên bản, bản vẽ (số, ngày).")
    col = kb.COT_MA_TRAN.get(loai, "GD")
    B = [m["code"] for m in kb.MUC if kb.muc_ap_dung(m["code"], col, quy_mo) == "B"]
    D = [m["code"] for m in kb.MUC if kb.muc_ap_dung(m["code"], col, quy_mo) == "Đ"]
    v.pham_vi_v3 = dict(B=B, D=D)
    if thieu_chan:
        v.ket_luan = V2_THIEU
        v.nhan_xet = ("Chưa thấy " + "; ".join(c["ten"].lower() for c in thieu_chan) +
                      ". Đề nghị bổ sung trước, sau đó mới kiểm tra chi tiết.")
    elif lam_ro:
        v.ket_luan = V2_LAM_RO
        v.nhan_xet = "Các thành phần cơ bản đã có; còn " + "; ".join(c["ten"].lower() for c in lam_ro) + " cần làm rõ."
    else:
        v.ket_luan = V2_DU
        v.nhan_xet = "Các thành phần cơ bản đều có trong danh mục."
    if quy_mo != "lon" and v.ket_luan != V2_THIEU:
        v.nhan_xet += (f" {kb.QUY_MO_NGAN[quy_mo]}: vòng 3 chỉ xét {len(B)} mục bắt buộc và {len(D)} mục đối chiếu, "
                       "không yêu cầu lập lại danh mục đủ Phụ lục VII.")
    return v


# ----------------------------------------------------------------------------- tin nhắn Zalo (chữ thường, không markdown)
def tin_nhan(v1=None, v2=None, info=None):
    info = info or {}
    nd = (v1.nhan_dien if v1 else {}) or {}
    du_an = info.get("du_an") or nd.get("du_an") or ""
    nt = info.get("nha_thau") or nd.get("nha_thau") or ""
    L = [f"Gửi đoàn TVGS{(' dự án ' + du_an) if du_an else ''},",
         f"P.KT đã kiểm tra hồ sơ chất lượng{(' của ' + nt) if nt else ''}:"]
    if v1 is not None and (v1.tra_lai or v2 is None):
        L.append(f"+ Vòng 1 – kiểm tra đầu vào: {v1.ket_luan}")
        for m in [m for m in v1.muc if m["muc"] == TRA_LAI] + [m for m in v1.muc if m["muc"] != TRA_LAI][:4]:
            L.append(f"- {(m['tep'] + ': ') if m.get('tep') else ''}{m['noi_dung']} → {m['xu_ly']}")
        if v1.tra_lai:
            L.append("+ Khi gửi lại:")
            L += ["- " + x for x in GOI_Y_GUI_LAI[:3]]
    elif v1 is not None and v1.muc:
        loai = [t["ten"] for t in v1.tep if not t["doc_duoc"]]
        if loai:
            L.append(f"+ Vòng 1 – kiểm tra đầu vào: {len(loai)} file không đọc được (" + "; ".join(loai) +
                     ") – đề nghị gửi lại bản Word/Excel gốc hoặc PDF có chữ.")
    if v2 is not None:
        L.append(f"+ Vòng 2 – rà soát sơ bộ ({kb.QUY_MO_NGAN.get(v2.quy_mo, '')}"
                 f"{', thầu phụ' if v2.vai_tro == 'phu' else ''}): {v2.ket_luan}")
        thieu = [c for c in v2.thanh_phan if c["trang_thai"] != "co"]
        if thieu:
            L.append("+ Đề nghị bổ sung / làm rõ:")
            L += ["- " + q for q in v2.cau_hoi]
        else:
            L.append("- Các thành phần cơ bản đã có, P.KT chuyển sang kiểm tra chi tiết.")
    L.append("Trân trọng.")
    return "\n".join(L)
